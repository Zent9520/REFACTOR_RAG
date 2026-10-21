import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from backend.app.modules.company.contract.scripts.setup_legal_fts import setup


class SetupLegalFtsTest(unittest.TestCase):

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
            VALUES (?, ?, ?, ?, CAST(? AS JSON), TIMESTAMP '2026-01-01')
            """,
            [
                1,
                "law-1",
                "Full legal document text.",
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
        self.source_rows = connection.execute(
            "SELECT * FROM legal_documents ORDER BY row_index"
        ).fetchall()
        connection.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_setup_and_rebuild_preserve_source_data(self):
        with contextlib.redirect_stdout(io.StringIO()):
            setup(
                db_path=self.db_path,
                rebuild=False,
                validation_query="contract penalties",
            )
            setup(
                db_path=self.db_path,
                rebuild=True,
                validation_query="contract penalties",
            )

        connection = duckdb.connect(
            str(self.db_path),
            read_only=True,
        )
        connection.execute("LOAD fts")
        source_rows = connection.execute(
            "SELECT * FROM legal_documents ORDER BY row_index"
        ).fetchall()
        search_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE legal_search"
            ).fetchall()
        }
        result = connection.execute(
            """
            SELECT document_id
            FROM (
                SELECT
                    document_id,
                    fts_main_legal_search.match_bm25(
                        document_id,
                        'contract penalties'
                    ) AS score
                FROM legal_search
            ) AS ranked
            WHERE score IS NOT NULL
            ORDER BY score DESC
            LIMIT 1
            """
        ).fetchone()
        connection.close()

        self.assertEqual(source_rows, self.source_rows)
        self.assertNotIn("vn_text", search_columns)
        self.assertEqual(result, ("law-1",))
