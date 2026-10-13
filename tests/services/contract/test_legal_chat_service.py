import unittest
from unittest.mock import AsyncMock, patch

from backend.app.modules.configuration.enums.prompt_code import PromptCode
from backend.app.modules.contract.services.legal_chat_service import LegalChatService


class LegalChatServiceTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.service = LegalChatService.__new__(LegalChatService)
        self.service.llm = AsyncMock()

    def test_analyzer_seeds_are_filtered_and_limited_to_six(self):
        result = self.service._validate_analyzer_result(
            {
                "metadata_seeds": {
                    "legal_area": [" area ", ""],
                    "unsupported": ["ignored"],
                    "title": ["one", "two", "three"],
                    "article_titles": ["four", "five", "six"],
                }
            }
        )

        self.assertEqual(
            result,
            {
                "legal_area": ["area"],
                "title": ["one", "two", "three"],
                "article_titles": ["four", "five"],
            },
        )

    def test_analyzer_rejects_empty_valid_seeds(self):
        with self.assertRaisesRegex(
            ValueError,
            "at least one valid seed",
        ):
            self.service._validate_analyzer_result(
                {
                    "metadata_seeds": {
                        "unsupported": ["seed"],
                        "title": ["  "],
                    }
                }
            )

    async def test_chat_returns_answer_seeds_and_sources_without_text(self):
        model = type("Model", (), {"model_name": "deployment"})()
        config = type(
            "Config",
            (),
            {"temperature": 0.2, "max_tokens": 2000},
        )()
        query_prompt = type(
            "Prompt",
            (),
            {
                "system_prompt": "Query system",
                "user_prompt": (
                    "Question: {{question}}\n"
                    "Contract: {{extracted_contract}}"
                ),
            },
        )()
        answer_prompt = type(
            "Prompt",
            (),
            {
                "system_prompt": "Answer system",
                "user_prompt": (
                    "Question: {{question}}\n"
                    "Contract: {{extracted_contract}}\n"
                    "Context: {{legal_context}}"
                ),
            },
        )()
        document = {
            "document_id": "law-1",
            "metadata": {"title": "Law title"},
            "vn_text": "Full legal text",
        }
        self.service.llm.chat_json.return_value = (
            '{"metadata_seeds":{"title":["contract penalty"]}}'
        )
        self.service.llm.chat.return_value = "Legal answer"

        async def load_prompt(db, prompt_code):
            return {
                PromptCode.LEGAL_CHAT_QUERY_ANALYZER: query_prompt,
                PromptCode.LEGAL_CHAT_ANSWER: answer_prompt,
            }[prompt_code]

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
            patch(
                "app.services.contract.legal_chat_service."
                "LegalChatRetrievalService.retrieve",
                return_value=[document],
            ) as retrieve,
        ):
            result = await self.service.chat(
                db=None,
                model_id=None,
                question="Is this penalty valid?",
                extracted_contract="Contract body",
            )

        retrieve.assert_called_once_with(
            {"title": ["contract penalty"]}
        )
        self.assertEqual(
            load_prompt_mock.await_args_list[0].kwargs["prompt_code"],
            PromptCode.LEGAL_CHAT_QUERY_ANALYZER,
        )
        self.assertEqual(
            load_prompt_mock.await_args_list[1].kwargs["prompt_code"],
            PromptCode.LEGAL_CHAT_ANSWER,
        )
        answer_messages = self.service.llm.chat.await_args.kwargs[
            "messages"
        ]
        answer_user_prompt = answer_messages[1]["content"]
        self.assertIn("Is this penalty valid?", answer_user_prompt)
        self.assertIn("Contract body", answer_user_prompt)
        self.assertIn("Full legal text", answer_user_prompt)
        self.assertEqual(
            result,
            {
                "answer": "Legal answer",
                "retrieval_seeds": {
                    "title": ["contract penalty"]
                },
                "sources": [
                    {
                        "document_id": "law-1",
                        "metadata": {"title": "Law title"},
                    }
                ],
            },
        )
        self.assertNotIn("vn_text", result["sources"][0])

    async def test_empty_retrieval_skips_answer_model(self):
        model = type("Model", (), {"model_name": "deployment"})()
        config = type(
            "Config",
            (),
            {"temperature": 0.2, "max_tokens": 2000},
        )()
        query_prompt = type(
            "Prompt",
            (),
            {
                "system_prompt": "Query system",
                "user_prompt": "{{question}} {{extracted_contract}}",
            },
        )()
        self.service.llm.chat_json.return_value = (
            '{"metadata_seeds":{"title":["missing"]}}'
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
                new=AsyncMock(return_value=query_prompt),
            ) as load_prompt,
            patch(
                "app.services.contract.legal_chat_service."
                "LegalChatRetrievalService.retrieve",
                return_value=[],
            ),
        ):
            result = await self.service.chat(
                db=None,
                model_id=None,
                question="Question",
                extracted_contract="Contract",
            )

        self.assertEqual(load_prompt.await_count, 1)
        self.service.llm.chat.assert_not_awaited()
        self.assertEqual(result["sources"], [])
        self.assertEqual(
            result["answer"],
            LegalChatService.EMPTY_RETRIEVAL_ANSWER,
        )
