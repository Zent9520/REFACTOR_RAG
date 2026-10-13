import argparse
import os
import sys
from pathlib import Path
from time import perf_counter

import duckdb


BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = os.getenv(
    "LEGAL_DB_PATH",
    "./data/legal_vbpl.duckdb",
)
DEFAULT_VALIDATION_QUERY = "phat vi pham hop dong"
FTS_SCHEMA = "fts_main_legal_search"


def resolve_db_path(raw_path: str) -> Path:
    db_path = Path(raw_path).expanduser()

    if not db_path.is_absolute():
        db_path = BACKEND_DIR / db_path

    return db_path.resolve()


def table_exists(connection, table_name: str) -> bool:
    return connection.execute(
        """
        SELECT COUNT(*) > 0
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table_name],
    ).fetchone()[0]


def schema_exists(connection, schema_name: str) -> bool:
    return connection.execute(
        """
        SELECT COUNT(*) > 0
        FROM information_schema.schemata
        WHERE schema_name = ?
        """,
        [schema_name],
    ).fetchone()[0]


def install_and_load_fts(connection) -> str:
    connection.execute("INSTALL fts")
    connection.execute("LOAD fts")

    row = connection.execute(
        """
        SELECT extension_version
        FROM duckdb_extensions()
        WHERE extension_name = 'fts'
        """
    ).fetchone()

    return row[0] if row and row[0] else "unknown"


def validate_source(connection) -> int:
    if not table_exists(connection, "legal_documents"):
        raise RuntimeError(
            "Required table legal_documents does not exist."
        )

    document_count = connection.execute(
        "SELECT COUNT(*) FROM legal_documents"
    ).fetchone()[0]
    duplicate_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT document_id
            FROM legal_documents
            GROUP BY document_id
            HAVING COUNT(*) > 1
        ) AS duplicates
        """
    ).fetchone()[0]

    if duplicate_count:
        raise RuntimeError(
            "legal_documents contains duplicate document_id values; "
            "legal_search requires a unique document identifier."
        )

    return document_count


def drop_search_structures(connection) -> None:
    if schema_exists(connection, FTS_SCHEMA):
        connection.execute(
            "PRAGMA drop_fts_index('legal_search')"
        )

    connection.execute("DROP TABLE IF EXISTS legal_search")


def populate_legal_search(connection) -> int:
    connection.execute(
        """
        CREATE TABLE legal_search (
            document_id VARCHAR PRIMARY KEY,
            doc_type VARCHAR,
            doc_number VARCHAR,
            year VARCHAR,
            issuer VARCHAR,
            issuer_kind VARCHAR,
            tier VARCHAR,
            tier_name VARCHAR,
            legal_area VARCHAR,
            title VARCHAR,
            issue_date VARCHAR,
            effective_date VARCHAR,
            status VARCHAR,
            update_date VARCHAR,
            signer VARCHAR,
            issuing_body VARCHAR,
            parent_acts VARCHAR,
            article_titles VARCHAR,
            citations VARCHAR,
            search_text VARCHAR
        )
        """
    )
    connection.execute(
        """
        INSERT INTO legal_search
        WITH extracted AS (
            SELECT
                document_id,
                COALESCE(json_extract_string(metadata, '$.doc_type'), '') AS doc_type,
                COALESCE(json_extract_string(metadata, '$.doc_number'), '') AS doc_number,
                COALESCE(json_extract_string(metadata, '$.year'), '') AS year,
                COALESCE(json_extract_string(metadata, '$.issuer'), '') AS issuer,
                COALESCE(json_extract_string(metadata, '$.issuer_kind'), '') AS issuer_kind,
                COALESCE(json_extract_string(metadata, '$.tier'), '') AS tier,
                COALESCE(json_extract_string(metadata, '$.tier_name'), '') AS tier_name,
                COALESCE(json_extract_string(metadata, '$.legal_area'), '') AS legal_area,
                COALESCE(json_extract_string(metadata, '$.title'), '') AS title,
                COALESCE(json_extract_string(metadata, '$.issue_date'), '') AS issue_date,
                COALESCE(json_extract_string(metadata, '$.effective_date'), '') AS effective_date,
                COALESCE(json_extract_string(metadata, '$.status'), '') AS status,
                COALESCE(json_extract_string(metadata, '$.update_date'), '') AS update_date,
                COALESCE(json_extract_string(metadata, '$.signer'), '') AS signer,
                COALESCE(json_extract_string(metadata, '$.issuing_body'), '') AS issuing_body,
                COALESCE(CAST(json_extract(metadata, '$.parent_acts') AS VARCHAR), '') AS parent_acts,
                COALESCE(CAST(json_extract(metadata, '$.article_titles') AS VARCHAR), '') AS article_titles,
                COALESCE(CAST(json_extract(metadata, '$.citations') AS VARCHAR), '') AS citations
            FROM legal_documents
        )
        SELECT
            *,
            concat_ws(
                ' ',
                doc_type,
                legal_area,
                title,
                article_titles,
                citations,
                parent_acts,
                issuing_body
            ) AS search_text
        FROM extracted
        """
    )

    return connection.execute(
        "SELECT COUNT(*) FROM legal_search"
    ).fetchone()[0]


def build_fts_index(connection) -> None:
    connection.execute(
        """
        PRAGMA create_fts_index(
            'legal_search',
            'document_id',
            'doc_type',
            'legal_area',
            'title',
            'article_titles',
            'citations',
            'parent_acts',
            'issuing_body',
            'search_text',
            stemmer = 'none',
            stopwords = 'none',
            ignore = '(\\.|[^a-z0-9À-ỹ])+',
            strip_accents = 1,
            lower = 1
        )
        """
    )


def validate_index(connection, query: str):
    return connection.execute(
        """
        SELECT document_id, score, title, legal_area
        FROM (
            SELECT
                document_id,
                title,
                legal_area,
                fts_main_legal_search.match_bm25(
                    document_id,
                    ?
                ) AS score
            FROM legal_search
        ) AS ranked
        WHERE score IS NOT NULL
        ORDER BY score DESC
        LIMIT 1
        """,
        [query],
    ).fetchone()


def setup(db_path: Path, rebuild: bool, validation_query: str) -> None:
    if not db_path.is_file():
        raise FileNotFoundError(
            f"Legal DuckDB not found: {db_path}"
        )

    total_started_at = perf_counter()
    connection = duckdb.connect(str(db_path))

    try:
        print(f"Database: {db_path}")
        print(f"DuckDB version: {duckdb.__version__}")
        fts_version = install_and_load_fts(connection)
        print(f"FTS extension version: {fts_version}")

        source_count = validate_source(connection)
        print(f"Legal documents: {source_count}")

        search_exists = table_exists(
            connection,
            "legal_search",
        )
        index_exists = schema_exists(
            connection,
            FTS_SCHEMA,
        )

        if search_exists and index_exists and not rebuild:
            print(
                "FTS index already exists; use --rebuild "
                "to recreate it."
            )
        else:
            if rebuild or search_exists or index_exists:
                print("Removing existing legal search structures...")
                drop_search_structures(connection)

            print("Building legal_search...")
            populate_started_at = perf_counter()
            search_count = populate_legal_search(connection)
            print(f"legal_search populated: {search_count}")
            print(
                "Populate duration: "
                f"{perf_counter() - populate_started_at:.3f}s"
            )

            if search_count != source_count:
                raise RuntimeError(
                    "legal_search row count does not match "
                    "legal_documents."
                )

            print("Building FTS index...")
            fts_started_at = perf_counter()
            build_fts_index(connection)
            print("FTS index ready.")
            print(
                f"FTS duration: {perf_counter() - fts_started_at:.3f}s"
            )

        search_count = connection.execute(
            "SELECT COUNT(*) FROM legal_search"
        ).fetchone()[0]
        final_source_count = connection.execute(
            "SELECT COUNT(*) FROM legal_documents"
        ).fetchone()[0]

        if final_source_count != source_count:
            raise RuntimeError(
                "legal_documents row count changed during setup."
            )

        print(f"legal_search count: {search_count}")
        validation_started_at = perf_counter()
        result = validate_index(
            connection,
            validation_query,
        )
        print(
            "Validation query duration: "
            f"{perf_counter() - validation_started_at:.3f}s"
        )
        print(f"Validation query: {validation_query}")

        if result is None:
            print("Validation result: no matching document")
        else:
            document_id, score, title, legal_area = result
            print(f"document_id: {document_id}")
            print(f"score: {score}")
            print(f"title: {title}")
            print(f"legal_area: {legal_area}")

        print(f"Total setup time: {perf_counter() - total_started_at:.3f}s")
    finally:
        connection.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the persistent DuckDB FTS index used by "
            "legal contract retrieval."
        )
    )
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=(
            "Path to legal_vbpl.duckdb. Defaults to LEGAL_DB_PATH "
            "or ./data/legal_vbpl.duckdb."
        ),
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop and recreate legal_search and its FTS index.",
    )
    parser.add_argument(
        "--validation-query",
        default=DEFAULT_VALIDATION_QUERY,
        help="Query used to validate the completed FTS index.",
    )
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    try:
        setup(
            db_path=resolve_db_path(args.db_path),
            rebuild=args.rebuild,
            validation_query=args.validation_query,
        )
    except Exception as exc:
        print(f"Legal FTS setup failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
