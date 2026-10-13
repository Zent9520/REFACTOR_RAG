from pathlib import Path
import sys

import duckdb


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "legal_vbpl.duckdb"


SAMPLE_DOCUMENTS = [
    {
        "row_index": 0,
        "document_id": "370952",
        "vn_text": """
QUYẾT ĐỊNH

Ban hành Danh mục dịch vụ sự nghiệp công sử dụng ngân sách nhà nước.

Điều 1. Ban hành kèm theo Quyết định này Danh mục dịch vụ sự nghiệp công.

Điều 2. Tổ chức thực hiện.

Điều 3. Quyết định này có hiệu lực thi hành kể từ ngày ký.
""".strip(),
        "en_text": None,
        "metadata": """
{
  "id": "370952",
  "doc_type": "Quyết định",
  "doc_number": null,
  "year": null,
  "issuer": "TTg",
  "issuer_kind": "Thủ tướng",
  "tier": 1,
  "tier_name": "central decisions & directives",
  "legal_area": "Tai chinh nha nuoc",
  "section": "van-ban",
  "title": "Quyet dinh 2099 QD TTg 2017 dich vu su nghiep cong su dung ngan sach nha nuoc Bo Khoa hoc",
  "source": "thuvienphapluat.vn",
  "is_english": false,
  "has_english": false,
  "issue_date": "27/12/2017",
  "effective_date": null,
  "status": null,
  "signer": "Vũ Đức Đam",
  "issuing_body": "Thủ tướng Chính phủ",
  "parent_acts": [],
  "article_titles": [
    "Ban hành kèm theo Quyết định này Danh mục dịch vụ sự nghiệp",
    "Tổ chức thực hiện",
    "Quyết định này có hiệu lực thi hành kể từ ngày ký."
  ],
  "citations": [
    {
      "diem": null,
      "dieu": null,
      "khoan": null,
      "kind": "external_mention",
      "raw": "Nghị định số 95/2017/NĐ-CP",
      "source": "preamble",
      "target": "Nghị định số 95/2017/NĐ-CP"
    }
  ]
}
""".strip(),
    },
    {
        "row_index": 1,
        "document_id": "694865",
        "vn_text": """
QUYẾT ĐỊNH

Công bố thủ tục hành chính lĩnh vực Thủy sản.

Điều 1. Công bố kèm theo Quyết định này các thủ tục hành chính.

Điều 2. Quyết định này có hiệu lực theo quy định.
""".strip(),
        "en_text": None,
        "metadata": """
{
  "id": "694865",
  "doc_type": "Quyết định",
  "doc_number": null,
  "year": null,
  "issuer": "UBND",
  "issuer_kind": "UBND tỉnh/TP",
  "tier": 2,
  "tier_name": "provincial & administrative",
  "legal_area": "Bo may hanh chinh",
  "section": "van-ban",
  "title": "Quyet dinh 601 QD UBND 2026 cong bo thu tuc hanh chinh linh vuc Thuy san cap tinh Lam Dong",
  "source": "thuvienphapluat.vn",
  "is_english": false,
  "has_english": false,
  "issue_date": "11/02/2026",
  "effective_date": null,
  "status": null,
  "issuing_body": "Tỉnh Lâm Đồng",
  "parent_acts": [
    "Luật số 31/2024/QH15"
  ],
  "article_titles": [],
  "citations": [
    {
      "diem": null,
      "dieu": null,
      "khoan": null,
      "kind": "external_mention",
      "raw": "Luật Thủy sản số 18/2017/QH14",
      "source": "preamble",
      "target": "Luật Thủy sản số 18/2017/QH14"
    }
  ]
}
""".strip(),
    },
]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = duckdb.connect(str(DB_PATH))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS legal_documents (
            row_index BIGINT,
            document_id VARCHAR,
            vn_text VARCHAR,
            en_text VARCHAR,
            metadata JSON,
            created_at TIMESTAMP
        )
    """)

    conn.execute("DELETE FROM legal_documents")

    for document in SAMPLE_DOCUMENTS:
        conn.execute(
            """
            INSERT INTO legal_documents (
                row_index,
                document_id,
                vn_text,
                en_text,
                metadata,
                created_at
            )
            VALUES (?, ?, ?, ?, CAST(? AS JSON), CURRENT_TIMESTAMP)
            """,
            [
                document["row_index"],
                document["document_id"],
                document["vn_text"],
                document["en_text"],
                document["metadata"],
            ],
        )

    count = conn.execute(
        "SELECT COUNT(*) FROM legal_documents"
    ).fetchone()[0]

    print(f"DuckDB created: {DB_PATH}")
    print(f"legal_documents rows: {count}")

    rows = conn.execute("""
        SELECT
            document_id,
            json_extract_string(metadata, '$.doc_type') AS doc_type,
            json_extract_string(metadata, '$.legal_area') AS legal_area,
            json_extract_string(metadata, '$.title') AS title
        FROM legal_documents
    """).fetchall()

    for row in rows:
        print(row)

    conn.close()


if __name__ == "__main__":
    main()
