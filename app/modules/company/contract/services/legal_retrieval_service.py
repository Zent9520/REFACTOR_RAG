import asyncio
import json
from pathlib import Path
from time import perf_counter
from typing import Any

import duckdb

from backend.app.modules.company.contract.contract_advanced_logging import (
    contract_advanced_logger as logger,
)
from backend.app.core.settings import settings


class LegalRetrievalService:

    LEGAL_TOP_K = 1
    LEGAL_FTS_CONCURRENCY = 4
    FTS_SCHEMA = "fts_main_legal_search"

    SUPPORTED_METADATA_FIELDS = {
        "doc_type",
        "doc_number",
        "year",
        "issuer",
        "issuer_kind",
        "tier",
        "tier_name",
        "legal_area",
        "section",
        "title",
        "source",
        "url",
        "issue_date",
        "effective_date",
        "status",
        "update_date",
        "signer",
        "issuing_body",
        "parent_acts",
        "article_titles",
        "citations",
    }

    @classmethod
    def retrieve(
        cls,
        legal_checks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        if not legal_checks:
            return []

        db_path = cls._resolve_db_path()
        total_started_at = perf_counter()
        cls._validate_database(db_path)
        fts_started_at = perf_counter()
        ranked_ids_by_check = []
        query_durations = []

        for check_index, check in enumerate(
            legal_checks,
            start=1,
        ):
            document_ids, duration = cls._run_search_one_check(
                db_path=db_path,
                check=check,
                check_index=check_index,
                check_count=len(legal_checks),
            )
            ranked_ids_by_check.append(document_ids)
            query_durations.append(duration)

        return cls._finish_retrieval(
            db_path=db_path,
            legal_checks=legal_checks,
            ranked_ids_by_check=ranked_ids_by_check,
            fts_query_sum=sum(query_durations),
            fts_wall_time=perf_counter() - fts_started_at,
            total_started_at=total_started_at,
        )

    @classmethod
    async def retrieve_async(
        cls,
        legal_checks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        if not legal_checks:
            return []

        db_path = cls._resolve_db_path()
        total_started_at = perf_counter()
        await asyncio.to_thread(
            cls._validate_database,
            db_path,
        )
        semaphore = asyncio.Semaphore(
            cls.LEGAL_FTS_CONCURRENCY
        )

        async def search_one(
            index: int,
            check: dict[str, Any],
        ):
            async with semaphore:
                try:
                    document_ids, duration = await asyncio.to_thread(
                        cls._run_search_one_check,
                        db_path,
                        check,
                        index + 1,
                        len(legal_checks),
                    )
                except Exception:
                    logger.exception(
                        "[LEGAL_RETRIEVAL] FTS search failed "
                        "legal_check_index=%d",
                        index,
                    )
                    raise

                return index, document_ids, duration

        fts_started_at = perf_counter()
        search_results = await asyncio.gather(
            *[
                search_one(index, check)
                for index, check in enumerate(legal_checks)
            ]
        )
        fts_wall_time = perf_counter() - fts_started_at
        search_results.sort(key=lambda item: item[0])

        return await cls._finish_retrieval_async(
            db_path=db_path,
            legal_checks=legal_checks,
            ranked_ids_by_check=[
                item[1] for item in search_results
            ],
            fts_query_sum=sum(
                item[2] for item in search_results
            ),
            fts_wall_time=fts_wall_time,
            total_started_at=total_started_at,
        )

    @classmethod
    def _resolve_db_path(cls) -> Path:
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
    def _validate_database(cls, db_path: Path) -> None:
        connection = duckdb.connect(
            str(db_path),
            read_only=True,
        )

        try:
            cls._load_and_validate_fts(connection)
        finally:
            connection.close()

    @classmethod
    def _run_search_one_check(
        cls,
        db_path: Path,
        check: dict[str, Any],
        check_index: int,
        check_count: int,
    ) -> tuple[list[str], float]:
        started_at = perf_counter()
        logger.info(
            "[CONTRACT_ADVANCED] legal_retrieval started "
            "check=%d/%d contract_text=%s",
            check_index,
            check_count,
            check["contract_text"],
        )
        document_ids = cls._search_one_check(
            db_path=db_path,
            check=check,
        )
        duration = perf_counter() - started_at
        logger.info(
            "[CONTRACT_ADVANCED] legal_retrieval completed "
            "check=%d/%d in %.3fs result_count=%d",
            check_index,
            check_count,
            duration,
            len(document_ids),
        )

        return document_ids, duration

    @classmethod
    def _search_one_check(
        cls,
        db_path: Path,
        check: dict[str, Any],
    ) -> list[str]:
        connection = duckdb.connect(
            str(db_path),
            read_only=True,
        )

        try:
            connection.execute("LOAD fts")
            return cls._search_document_ids(
                connection=connection,
                metadata_seeds=check.get(
                    "metadata_seeds",
                    {},
                ),
            )
        finally:
            connection.close()

    @classmethod
    def _finish_retrieval(
        cls,
        db_path: Path,
        legal_checks: list[dict[str, Any]],
        ranked_ids_by_check: list[list[str]],
        fts_query_sum: float,
        fts_wall_time: float,
        total_started_at: float,
    ) -> list[dict[str, Any]]:
        unique_document_ids = list(
            dict.fromkeys(
                document_id
                for document_ids in ranked_ids_by_check
                for document_id in document_ids
            )
        )
        document_load_started_at = perf_counter()
        documents = {
            document["document_id"]: document
            for document in cls._load_documents_once(
                db_path=db_path,
                document_ids=unique_document_ids,
            )
        }
        document_load_duration = (
            perf_counter() - document_load_started_at
        )
        logger.info(
            "[LEGAL_RETRIEVAL][TIMING] "
            "fts_query_sum=%.3fs fts_wall_time=%.3fs "
            "document_load=%.3fs total=%.3fs",
            fts_query_sum,
            fts_wall_time,
            document_load_duration,
            perf_counter() - total_started_at,
        )

        return cls._build_results(
            legal_checks=legal_checks,
            ranked_ids_by_check=ranked_ids_by_check,
            documents=documents,
        )

    @classmethod
    async def _finish_retrieval_async(
        cls,
        db_path: Path,
        legal_checks: list[dict[str, Any]],
        ranked_ids_by_check: list[list[str]],
        fts_query_sum: float,
        fts_wall_time: float,
        total_started_at: float,
    ) -> list[dict[str, Any]]:
        unique_document_ids = list(
            dict.fromkeys(
                document_id
                for document_ids in ranked_ids_by_check
                for document_id in document_ids
            )
        )
        document_load_started_at = perf_counter()
        loaded_documents = await asyncio.to_thread(
            cls._load_documents_once,
            db_path,
            unique_document_ids,
        )
        document_load_duration = (
            perf_counter() - document_load_started_at
        )
        documents = {
            document["document_id"]: document
            for document in loaded_documents
        }
        logger.info(
            "[LEGAL_RETRIEVAL][TIMING] "
            "fts_query_sum=%.3fs fts_wall_time=%.3fs "
            "document_load=%.3fs total=%.3fs",
            fts_query_sum,
            fts_wall_time,
            document_load_duration,
            perf_counter() - total_started_at,
        )

        return cls._build_results(
            legal_checks=legal_checks,
            ranked_ids_by_check=ranked_ids_by_check,
            documents=documents,
        )

    @staticmethod
    def _build_results(
        legal_checks: list[dict[str, Any]],
        ranked_ids_by_check: list[list[str]],
        documents: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "contract_text": check["contract_text"],
                "contexts": [
                    documents[document_id]
                    for document_id in document_ids
                    if document_id in documents
                ],
            }
            for check, document_ids in zip(
                legal_checks,
                ranked_ids_by_check,
            )
        ]

    @classmethod
    def _load_documents_once(
        cls,
        db_path: Path,
        document_ids: list[str],
    ) -> list[dict[str, Any]]:
        if not document_ids:
            return []

        connection = duckdb.connect(
            str(db_path),
            read_only=True,
        )

        try:
            return cls._load_documents(
                connection=connection,
                document_ids=document_ids,
            )
        finally:
            connection.close()

    @classmethod
    def _load_and_validate_fts(
        cls,
        connection,
    ) -> None:

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
    def _search_document_ids(
        cls,
        connection,
        metadata_seeds: Any,
    ) -> list[str]:

        normalized_seeds = cls._normalize_seeds(
            metadata_seeds
        )

        if not normalized_seeds:
            return []

        search_query = " ".join(
            seed
            for seeds in normalized_seeds.values()
            for seed in seeds
        )
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
            LIMIT {cls.LEGAL_TOP_K}
            """,
            [search_query],
        ).fetchall()

        return [row[0] for row in rows]

    @classmethod
    def _load_documents(
        cls,
        connection,
        document_ids: list[str],
    ) -> list[dict[str, Any]]:

        if not document_ids:
            return []

        placeholders = ", ".join(
            "?" for _ in document_ids
        )

        rows = connection.execute(
            f"""
            SELECT document_id, vn_text, metadata
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
            for document_id, vn_text, metadata in rows
        }

        return [
            documents[document_id]
            for document_id in document_ids
            if document_id in documents
        ]

    @classmethod
    def _normalize_seeds(
        cls,
        metadata_seeds: Any,
    ) -> dict[str, list[str]]:

        if not isinstance(metadata_seeds, dict):
            return {}

        normalized = {}

        for field, seeds in metadata_seeds.items():
            if (
                field not in cls.SUPPORTED_METADATA_FIELDS
                or not isinstance(seeds, list)
            ):
                continue

            values = [
                seed.strip()
                for seed in seeds
                if isinstance(seed, str)
                and seed.strip()
            ]

            if values:
                normalized[field] = values

        return normalized

    @staticmethod
    def _parse_metadata(
        raw_metadata: Any,
    ) -> dict[str, Any]:

        if isinstance(raw_metadata, dict):
            return raw_metadata

        if isinstance(raw_metadata, str):
            parsed = json.loads(raw_metadata)

            if isinstance(parsed, dict):
                return parsed

        raise ValueError(
            "Legal document metadata must be a JSON object."
        )
