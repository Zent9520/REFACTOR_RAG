import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb

from backend.app.core.settings import settings
from backend.app.shared.azure.azure_search_service import (
    AzureSearchService,
)
from backend.app.modules.company.contract.services.company_policy_retrieval_service import (
    CompanyPolicyRetrievalService,
)
from backend.app.modules.company.contract.services.legal_retrieval_service import (
    LegalRetrievalService,
)
from backend.app.modules.company.contract.scripts.setup_legal_fts import (
    build_fts_index,
    populate_legal_search,
)


class CompanyPolicyRetrievalServiceTest(
    unittest.IsolatedAsyncioTestCase
):

    async def test_empty_checks_do_not_call_azure_search(self):
        with patch.object(
            AzureSearchService,
            "retrieve_contract_policy",
        ) as retrieve:
            result = await CompanyPolicyRetrievalService.retrieve([])

        self.assertEqual(result, [])
        retrieve.assert_not_called()

    async def test_empty_context_preserves_company_check(self):
        with patch.object(
            AzureSearchService,
            "retrieve_contract_policy",
            return_value=[],
        ):
            result = await CompanyPolicyRetrievalService.retrieve(
                [
                    {
                        "contract_text": "Clause A",
                        "retrieval_seeds": ["approval"],
                    }
                ]
            )

        self.assertEqual(
            result,
            [{"contract_text": "Clause A", "contexts": []}],
        )

    async def test_uses_one_seed_top_one_and_preserves_mapping(self):
        first_context = {
            "chunk_id": "chunk-1",
            "parent_id": "document-1",
            "content": "Policy A",
        }
        second_context = {
            "chunk_id": "chunk-2",
            "parent_id": "document-2",
            "content": "Policy B",
        }

        def retrieve_policy(*, question, top_k):
            self.assertEqual(top_k, 1)
            return {
                "approval": [first_context],
                "authority": [second_context],
            }[question]

        with patch.object(
            AzureSearchService,
            "retrieve_contract_policy",
            side_effect=retrieve_policy,
        ) as retrieve:
            result = await CompanyPolicyRetrievalService.retrieve(
                [
                    {
                        "contract_text": "Clause A",
                        "retrieval_seeds": ["approval", "ignored"],
                    },
                    {
                        "contract_text": "Clause B",
                        "retrieval_seeds": ["authority", "ignored"],
                    },
                ]
            )

        self.assertEqual(retrieve.call_count, 2)
        self.assertEqual(
            result,
            [
                {
                    "contract_text": "Clause A",
                    "contexts": [first_context],
                },
                {
                    "contract_text": "Clause B",
                    "contexts": [second_context],
                },
            ],
        )


class LegalRetrievalServiceTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "legal.duckdb"
        connection = duckdb.connect(str(self.db_path))
        connection.execute(
            """
            CREATE TABLE legal_documents (
                row_index BIGINT,
                document_id VARCHAR,
                vn_text VARCHAR,
                en_text VARCHAR,
                metadata JSON,
                created_at TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            INSERT INTO legal_documents
            VALUES (?, ?, ?, ?, CAST(? AS JSON), CURRENT_TIMESTAMP)
            """,
            [
                1,
                "law-1",
                "Rules for commercial contract penalties.",
                None,
                json.dumps(
                    {
                        "doc_type": "Law",
                        "legal_area": "Commercial contracts",
                        "title": "Contract penalties",
                    }
                ),
            ],
        )
        connection.execute("LOAD fts")
        populate_legal_search(connection)
        build_fts_index(connection)
        connection.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_empty_checks_do_not_open_database(self):
        with patch.object(
            settings,
            "LEGAL_DB_PATH",
            "missing.duckdb",
        ):
            self.assertEqual(
                LegalRetrievalService.retrieve([]),
                [],
            )

    def test_local_duckdb_returns_ranked_document(self):
        with patch.object(
            settings,
            "LEGAL_DB_PATH",
            str(self.db_path),
        ):
            result = LegalRetrievalService.retrieve(
                [
                    {
                        "contract_text": "Penalty clause",
                        "metadata_seeds": {
                            "title": ["contract penalties"],
                        },
                    }
                ]
            )

        self.assertEqual(
            result[0]["contexts"][0]["document_id"],
            "law-1",
        )
        self.assertEqual(len(result[0]["contexts"]), 1)

    def test_missing_fts_index_has_setup_instruction(self):
        connection = duckdb.connect(str(self.db_path))
        connection.execute("LOAD fts")
        connection.execute(
            "PRAGMA drop_fts_index('legal_search')"
        )
        connection.execute("DROP TABLE legal_search")
        connection.close()

        with (
            patch.object(
                settings,
                "LEGAL_DB_PATH",
                str(self.db_path),
            ),
            self.assertRaisesRegex(
                RuntimeError,
                "setup_legal_fts.py --rebuild",
            ),
        ):
            LegalRetrievalService.retrieve(
                [
                    {
                        "contract_text": "Penalty clause",
                        "metadata_seeds": {
                            "title": ["contract penalties"],
                        },
                    }
                ]
            )

    def test_empty_context_preserves_legal_check(self):
        with patch.object(
            settings,
            "LEGAL_DB_PATH",
            str(self.db_path),
        ):
            result = LegalRetrievalService.retrieve(
                [
                    {
                        "contract_text": "Unknown clause",
                        "metadata_seeds": {
                            "title": ["zzzz-no-match"],
                        },
                    }
                ]
            )

        self.assertEqual(
            result,
            [
                {
                    "contract_text": "Unknown clause",
                    "contexts": [],
                }
            ],
        )

    def test_unknown_metadata_field_is_ignored(self):
        normalized = LegalRetrievalService._normalize_seeds(
            {
                "unknown_sql_field": ["untrusted"],
                "title": ["contract"],
            }
        )

        self.assertEqual(
            normalized,
            {"title": ["contract"]},
        )


class LegalRetrievalConcurrencyTest(
    unittest.IsolatedAsyncioTestCase
):

    async def test_async_retrieval_is_bounded_and_preserves_order(self):
        checks = [
            {
                "contract_text": f"Clause {index}",
                "metadata_seeds": {
                    "title": [f"query {index}"],
                },
            }
            for index in range(4)
        ]
        active = 0
        maximum_active = 0
        lock = threading.Lock()

        def search_one(
            db_path,
            check,
            check_index,
            check_count,
        ):
            nonlocal active, maximum_active

            with lock:
                active += 1
                maximum_active = max(maximum_active, active)

            time.sleep(0.01 * (5 - check_index))

            with lock:
                active -= 1

            return [f"law-{check_index}"], 0.01

        documents = [
            {
                "document_id": f"law-{index}",
                "metadata": {},
                "vn_text": f"Law {index}",
            }
            for index in range(1, 5)
        ]

        with (
            patch.object(
                LegalRetrievalService,
                "LEGAL_FTS_CONCURRENCY",
                2,
            ),
            patch.object(
                LegalRetrievalService,
                "_resolve_db_path",
                return_value=Path("legal.duckdb"),
            ),
            patch.object(
                LegalRetrievalService,
                "_validate_database",
            ),
            patch.object(
                LegalRetrievalService,
                "_run_search_one_check",
                side_effect=search_one,
            ),
            patch.object(
                LegalRetrievalService,
                "_load_documents_once",
                return_value=documents,
            ) as load_documents,
        ):
            result = await LegalRetrievalService.retrieve_async(
                checks
            )

        self.assertEqual(maximum_active, 2)
        self.assertEqual(
            [item["contract_text"] for item in result],
            [f"Clause {index}" for index in range(4)],
        )
        self.assertEqual(
            [
                item["contexts"][0]["document_id"]
                for item in result
            ],
            [f"law-{index}" for index in range(1, 5)],
        )
        load_documents.assert_called_once_with(
            Path("legal.duckdb"),
            [f"law-{index}" for index in range(1, 5)],
        )

    async def test_default_concurrency_is_four(self):
        self.assertEqual(
            LegalRetrievalService.LEGAL_FTS_CONCURRENCY,
            4,
        )
