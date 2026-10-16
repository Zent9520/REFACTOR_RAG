import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()


async def main():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        connect_args={"statement_cache_size": 0},
    )
    async with engine.connect() as conn:
        print("=== ai_models ===")
        res = await conn.execute(text(
            "SELECT id, code, provider, model_name, display_name, "
            "is_default, is_active, created_at "
            "FROM ai_models ORDER BY created_at"
        ))
        for r in res.fetchall():
            print(
                f"  id={r.id}\n"
                f"    code={r.code!r}  provider={r.provider!r}\n"
                f"    model_name={r.model_name!r}  display={r.display_name!r}\n"
                f"    default={r.is_default}  active={r.is_active}  created={r.created_at:%Y-%m-%d}"
            )

        print("\n=== model đang dùng theo workspace ===")
        res = await conn.execute(text(
            "SELECT w.code AS workspace, m.model_name, m.id AS model_id, "
            "c.temperature, c.max_tokens "
            "FROM workspace_model_configs c "
            "JOIN workspaces w ON w.id = c.workspace_id "
            "LEFT JOIN ai_models m ON m.id = c.model_id "
            "ORDER BY w.code"
        ))
        for r in res.fetchall():
            print(
                f"  {r.workspace}: model_name={r.model_name!r} "
                f"temp={r.temperature} max_tokens={r.max_tokens}\n"
                f"    model_id={r.model_id}"
            )
    await engine.dispose()


asyncio.run(main())