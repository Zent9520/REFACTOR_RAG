import json
from pathlib import Path
from typing import Any

import duckdb

from app.core.settings import settings


class LegalChatRetrievalService:
    LEGAL_CHAT_TOP_K = 4
    FTS_SCHEMA = "fts_main_legal_search"

    @classmethod
    def retrieve(
        cls,
        metadata_seeds: dict[str, list[str]],
    ) -> list[dict[str, Any]]:
        search_query = " ".join(
            seed
            for seeds in metadata_seeds.values()
            for seed in seeds
        )

        if not search_query:
            raise ValueError("Legal Chat FTS query must not be empty.")

        db_path = cls._resolve_db_path()
        connection = duckdb.connect(
            str(db_path),
            read_only=True,
        )

        try:
            cls._load_and_validate_fts(connection)
            rows = connection.execute(
                f"""
                SELECT document_id
                FROM (
                    SELECT
                        document_id,
                        fts_main_legal_search.match_bm25(
                            document_id,
                            ?
                        ) AS score
                    FROM legal_search
                ) AS ranked
                WHERE score IS NOT NULL
                ORDER BY score DESC
                LIMIT {cls.LEGAL_CHAT_TOP_K}
                """,
                [search_query],
            ).fetchall()
            document_ids = list(
                dict.fromkeys(row[0] for row in rows)
            )

            return cls._load_documents(
                connection=connection,
                document_ids=document_ids,
            )
        finally:
            connection.close()

    @staticmethod
    def _resolve_db_path() -> Path:
        db_path = Path(settings.LEGAL_DB_PATH).expanduser()

        if not db_path.is_absolute():
            backend_dir = Path(__file__).resolve().parents[3]
            db_path = backend_dir / db_path

        db_path = db_path.resolve()

        if not db_path.is_file():
            raise FileNotFoundError(
                f"Legal DuckDB not found: {db_path}"
            )

        return db_path

    @classmethod
    def _load_and_validate_fts(cls, connection) -> None:
        try:
            connection.execute("LOAD fts")
        except duckdb.Error as exc:
            raise RuntimeError(
                "DuckDB FTS extension is not available. Run "
                "python scripts/setup_legal_fts.py --rebuild first."
            ) from exc

        index_exists = connection.execute(
            """
            SELECT COUNT(*) > 0
            FROM information_schema.schemata
            WHERE schema_name = ?
            """,
            [cls.FTS_SCHEMA],
        ).fetchone()[0]

        if not index_exists:
            raise RuntimeError(
                "Legal FTS index is not initialized. Run "
                "python scripts/setup_legal_fts.py --rebuild first."
            )

    @classmethod
    def _load_documents(
        cls,
        connection,
        document_ids: list[str],
    ) -> list[dict[str, Any]]:
        if not document_ids:
            return []

        placeholders = ", ".join("?" for _ in document_ids)
        rows = connection.execute(
            f"""
            SELECT document_id, metadata, vn_text
            FROM legal_documents
            WHERE document_id IN ({placeholders})
            """,
            document_ids,
        ).fetchall()
        documents = {
            document_id: {
                "document_id": document_id,
                "metadata": cls._parse_metadata(metadata),
                "vn_text": vn_text,
            }
            for document_id, metadata, vn_text in rows
        }

        return [
            documents[document_id]
            for document_id in document_ids
            if document_id in documents
        ]

    @staticmethod
    def _parse_metadata(raw_metadata: Any) -> dict[str, Any]:
        if isinstance(raw_metadata, dict):
            return raw_metadata

        if isinstance(raw_metadata, str):
            try:
                parsed = json.loads(raw_metadata)
            except json.JSONDecodeError:
                return {}

            if isinstance(parsed, dict):
                return parsed

        return {}
