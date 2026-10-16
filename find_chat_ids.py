import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

SECRET_WORDS = ("token", "secret", "password", "key", "credential")
TABLES = ["microsoft_accounts", "users", "ai_models", "departments", "roles", "workspaces"]


def is_secret(col: str) -> bool:
    return any(w in col.lower() for w in SECRET_WORDS)


async def main():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        connect_args={"statement_cache_size": 0},
    )
    async with engine.connect() as conn:
        # 1. Cột nào trong DB có tên liên quan đến group / object / model
        res = await conn.execute(text(
            "SELECT table_name, column_name, data_type FROM information_schema.columns "
            "WHERE table_schema = 'public' AND ("
            "column_name ILIKE '%group%' OR column_name ILIKE '%object%' "
            "OR column_name ILIKE '%microsoft%' OR column_name ILIKE '%model%') "
            "ORDER BY table_name, column_name"
        ))
        print("=== CỘT LIÊN QUAN (group / object / microsoft / model) ===")
        for r in res.fetchall():
            print("  ", tuple(r))

        # 2. Vài dòng mẫu của từng bảng, bỏ cột nhạy cảm
        for table in TABLES:
            cols_res = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :t ORDER BY ordinal_position"
            ), {"t": table})
            cols = [c[0] for c in cols_res.fetchall()]
            safe = [c for c in cols if not is_secret(c)]
            hidden = [c for c in cols if is_secret(c)]
            if not safe:
                continue
            col_list = ", ".join(f'"{c}"' for c in safe)
            rows = (await conn.execute(text(f'SELECT {col_list} FROM "{table}" LIMIT 5'))).fetchall()
            print(f"\n=== {table} ({len(rows)} dòng mẫu) ===")
            if hidden:
                print("   (đã ẩn cột:", ", ".join(hidden) + ")")
            print("   cột:", safe)
            for row in rows:
                print("  ", tuple(row))
    await engine.dispose()


asyncio.run(main())