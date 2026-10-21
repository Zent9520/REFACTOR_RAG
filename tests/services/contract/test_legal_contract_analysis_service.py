import unittest
from unittest.mock import AsyncMock, patch

from backend.app.modules.configuration.enums.prompt_code import PromptCode
from backend.app.modules.company.contract.services.legal_contract_analysis_service import (
    LegalContractAnalysisService,
)
from backend.app.modules.company.contract.services.legal_azure_search_retrieval_service import (
    LegalAzureSearchRetrievalService,
)
from backend.app.shared.llm.bge_embedding import BGEEmbeddingService


class LegalContractAnalysisServiceTest(
    unittest.IsolatedAsyncioTestCase
):

    def setUp(self):
        self.service = LegalContractAnalysisService.__new__(
            LegalContractAnalysisService
        )
        self.service.llm = AsyncMock()

    def test_analyzer_validation_limits_checks_and_seeds(self):
        result = self.service._validate_analyzer_result(
            {
                "legal_checks": [
                    {
                        "contract_text": f"Clause {index}",
                        "metadata_seeds": {
                            "title": [
                                " first ",
                                "first",
                                "second",
                                "third",
                            ],
                            "unsupported": ["ignored"],
                        },
                    }
                    for index in range(10)
                ]
            }
        )

        self.assertEqual(len(result), 8)
        self.assertEqual(
            result[0]["seeds"],
            ["first", "second"],
        )
        print(
            "[TEST][LEGAL_ANALYZER] limited checks=8 and "
            "normalized unique seeds=['first', 'second']"
        )

    async def test_analyze_streams_each_check_sequentially(self):
        model = type("Model", (), {"model_name": "deployment"})()
        config = type(
            "Config",
            (),
            {"temperature": 0.2, "max_tokens": 2000},
        )()
        analyzer_prompt = type(
            "Prompt",
            (),
            {
                "system_prompt": "Analyzer system",
                "user_prompt": "{{extracted_contract}}",
            },
        )()
        reviewer_prompt = type(
            "Prompt",
            (),
            {
                "system_prompt": "Reviewer system",
                "user_prompt": "{{legal_review_data}}",
            },
        )()
        self.service.llm.chat_json.side_effect = [
            """
            {
              "legal_checks": [
                {
                  "contract_text": "Clause A",
                  "metadata_seeds": {"title": ["penalty"]}
                },
                {
                  "contract_text": "Clause B",
                  "metadata_seeds": {"legal_area": ["construction"]}
                }
              ]
            }
            """,
            """
            {
              "result": {
                "contract_text": "Clause A",
                "status": "RISK",
                "explanation": "Risk explanation",
                "recommendation": "Revise clause",
                "sources": [{"document_id": "law-1", "vn_text": "omit"}]
              }
            }
            """,
            """
            {
              "result": {
                "contract_text": "Clause B",
                "status": "COMPLIANT",
                "explanation": "Compliant explanation",
                "recommendation": "Keep clause",
                "sources": [{"document_id": "law-2"}]
              }
            }
            """,
        ]

        async def load_prompt(db, prompt_code):
            return {
                PromptCode.LEGAL_CONTRACT_ANALYZER: analyzer_prompt,
                PromptCode.LEGAL_CONTRACT_REVIEWER: reviewer_prompt,
            }[prompt_code]

        embedded_batches = []

        def embed_batch(texts):
            embedded_batches.append(list(texts))
            return [
                [float(index + 1)] * 1024
                for index, _ in enumerate(texts)
            ]

        retrieved_seed_groups = []

        def retrieve(seed_vectors):
            seeds = [item["seed"] for item in seed_vectors]
            retrieved_seed_groups.append(seeds)
            document_id = "law-1" if seeds == ["penalty"] else "law-2"
            return [
                {
                    "document_id": document_id,
                    "metadata": {"title": document_id},
                    "vn_text": f"Full text {document_id}",
                }
            ]

        with (
            patch.object(
                self.service,
                "_load_model_context",
                new=AsyncMock(return_value=(model, config)),
            ),
            patch.object(
                self.service,
                "_load_prompt",
                new=AsyncMock(side_effect=load_prompt),
            ) as load_prompt_mock,
            patch.object(
                BGEEmbeddingService,
                "embed_batch",
                side_effect=embed_batch,
            ) as embedding,
            patch.object(
                LegalAzureSearchRetrievalService,
                "retrieve_with_vectors",
                side_effect=retrieve,
            ) as retrieval,
        ):
            events = [
                event
                async for event in self.service.analyze(
                    db=None,
                    model_id=None,
                    output_extract="Contract body",
                )
            ]

        self.assertEqual(self.service.llm.chat_json.await_count, 3)
        self.assertEqual(embedding.call_count, 1)
        self.assertEqual(embedded_batches, [["penalty", "construction"]])
        self.assertEqual(retrieval.call_count, 2)
        self.assertEqual(
            retrieved_seed_groups,
            [["penalty"], ["construction"]],
        )
        self.assertEqual(load_prompt_mock.await_count, 2)
        self.assertEqual(
            load_prompt_mock.await_args_list[0].kwargs["prompt_code"],
            PromptCode.LEGAL_CONTRACT_ANALYZER,
        )
        self.assertEqual(
            load_prompt_mock.await_args_list[1].kwargs["prompt_code"],
            PromptCode.LEGAL_CONTRACT_REVIEWER,
        )
        first_reviewer_prompt = (
            self.service.llm.chat_json.await_args_list[1]
            .kwargs["messages"][1]["content"]
        )
        second_reviewer_prompt = (
            self.service.llm.chat_json.await_args_list[2]
            .kwargs["messages"][1]["content"]
        )
        self.assertIn("Full text law-1", first_reviewer_prompt)
        self.assertNotIn("Full text law-2", first_reviewer_prompt)
        self.assertIn("Full text law-2", second_reviewer_prompt)
        self.assertNotIn("Full text law-1", second_reviewer_prompt)
        self.assertEqual(
            [event["event"] for event in events],
            ["started", "result", "result", "completed"],
        )
        self.assertNotIn(
            "vn_text",
            events[1]["data"]["result"]["sources"][0],
        )
        print(
            "[TEST][LEGAL_BATCH] embedded one batch=2 seeds; "
            "mapping Clause A->penalty->law-1 and "
            "Clause B->construction->law-2 preserved"
        )

    async def test_empty_checks_skip_retrieval_and_reviewer(self):
        model = type("Model", (), {"model_name": "deployment"})()
        config = type(
            "Config",
            (),
            {"temperature": 0.2, "max_tokens": 2000},
        )()
        analyzer_prompt = type(
            "Prompt",
            (),
            {
                "system_prompt": "Analyzer system",
                "user_prompt": "{{extracted_contract}}",
            },
        )()
        self.service.llm.chat_json.return_value = (
            '{"legal_checks": []}'
        )

        with (
            patch.object(
                self.service,
                "_load_model_context",
                new=AsyncMock(return_value=(model, config)),
            ),
            patch.object(
                self.service,
                "_load_prompt",
                new=AsyncMock(return_value=analyzer_prompt),
            ) as load_prompt,
            patch.object(
                BGEEmbeddingService,
                "embed_batch",
            ) as embedding,
            patch.object(
                LegalAzureSearchRetrievalService,
                "retrieve_with_vectors",
            ) as retrieval,
        ):
            events = [
                event
                async for event in self.service.analyze(
                    db=None,
                    model_id=None,
                    output_extract="Contract body",
                )
            ]

        self.assertEqual(
            events,
            [
                {"event": "started", "data": {"total": 0}},
                {"event": "completed", "data": {"total": 0}},
            ],
        )
        self.assertEqual(self.service.llm.chat_json.await_count, 1)
        self.assertEqual(load_prompt.await_count, 1)
        embedding.assert_not_called()
        retrieval.assert_not_called()
        print(
            "[TEST][LEGAL_EMPTY] no checks; skipped BGE, Azure retrieval, "
            "and reviewer"
        )

    def test_legal_contract_top_k_is_four(self):
        self.assertEqual(
            LegalAzureSearchRetrievalService.TOP_K,
            4,
        )
        print("[TEST][LEGAL_RETRIEVAL] Azure Legal TOP_K=4")
