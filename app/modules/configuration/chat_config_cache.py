"""Process-local cache for configuration shared by chat requests."""

import asyncio
import logging
import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.modules.configuration.models.ai_model import AIModel
from app.modules.configuration.models.ai_prompt import AIPrompt
from app.modules.configuration.models.workspace import Workspace
from app.modules.configuration.models.workspace_model_config import WorkspaceModelConfig
from app.modules.configuration.models.workspace_rag_config import WorkspaceRagConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelSettings:
    provider: str
    model_name: str


@dataclass(frozen=True)
class WorkspaceModelSettings:
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class ChatConfigSnapshot:
    prompts: dict[str, str]
    models: dict[UUID, ModelSettings]
    model_configs: dict[str, WorkspaceModelSettings]
    top_k: dict[str, int]


class ChatConfigCache:
    """Load once, then refresh stale snapshots without blocking chat requests."""

    TTL_SECONDS = 60
    RETRY_SECONDS = 5

    _snapshot: ChatConfigSnapshot | None = None
    _loaded_at = 0.0
    _generation = 0
    _lock: asyncio.Lock | None = None
    _refresh_task: asyncio.Task | None = None

    @classmethod
    def invalidate(cls) -> None:
        # A refresh already in progress must not publish the old DB snapshot.
        cls._generation += 1
        cls._snapshot = None
        cls._loaded_at = 0.0

    @classmethod
    async def get(cls) -> ChatConfigSnapshot:
        snapshot = cls._snapshot
        age = time.monotonic() - cls._loaded_at
        if snapshot is None:
            return await cls.refresh()
        if age >= cls.TTL_SECONDS:
            cls._schedule_refresh()
        return snapshot

    @classmethod
    async def lookup(cls, section: str, key):
        snapshot = await cls.get()
        value = getattr(snapshot, section).get(key)
        if value is None:
            # A configuration may have been added since the last snapshot.
            snapshot = await cls.refresh(force=True)
            value = getattr(snapshot, section).get(key)
        return value

    @classmethod
    async def get_chat_settings(
        cls, prompt_code: str, model_id: UUID | str, workspace_code: str
    ) -> tuple[str | None, ModelSettings | None, WorkspaceModelSettings | None]:
        # ChatRequest.model_id is a string; SQLAlchemy returns UUID objects.
        # Normalize before looking up a model in the in-memory snapshot.
        try:
            model_key = model_id if isinstance(model_id, UUID) else UUID(str(model_id))
        except (TypeError, ValueError):
            model_key = None

        snapshot = await cls.get()
        if (
            prompt_code not in snapshot.prompts
            or (model_key is not None and model_key not in snapshot.models)
            or workspace_code not in snapshot.model_configs
        ):
            snapshot = await cls.refresh(force=True)
        return (
            snapshot.prompts.get(prompt_code),
            snapshot.models.get(model_key),
            snapshot.model_configs.get(workspace_code),
        )

    @classmethod
    def _schedule_refresh(cls) -> None:
        if cls._refresh_task is None or cls._refresh_task.done():
            cls._refresh_task = asyncio.create_task(cls._refresh_in_background())

    @classmethod
    async def _refresh_in_background(cls) -> None:
        started = time.perf_counter()
        try:
            await cls.refresh()
            logger.info("[chat_timing] stage=config_refresh duration=%.3fs", time.perf_counter() - started)
        except Exception:
            logger.exception("Chat configuration cache refresh failed")

    @classmethod
    async def refresh(cls, *, force: bool = False) -> ChatConfigSnapshot:
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        async with cls._lock:
            age = time.monotonic() - cls._loaded_at
            if cls._snapshot is not None and (
                (not force and age < cls.TTL_SECONDS)
                or (force and age < cls.RETRY_SECONDS)
            ):
                return cls._snapshot

            while True:
                generation = cls._generation
                snapshot = await cls._load()
                if generation == cls._generation:
                    break
                # An API committed a configuration change during the load.
            cls._snapshot = snapshot
            cls._loaded_at = time.monotonic()
            return snapshot

    @staticmethod
    async def _load() -> ChatConfigSnapshot:
        started = time.perf_counter()
        async with AsyncSessionLocal() as db:
            prompts = (await db.execute(
                select(AIPrompt.code, AIPrompt.system_prompt).where(AIPrompt.is_active.is_(True))
            )).all()
            models = (await db.execute(
                select(AIModel.id, AIModel.provider, AIModel.model_name)
            )).all()
            model_configs = (await db.execute(
                select(
                    Workspace.code,
                    WorkspaceModelConfig.temperature,
                    WorkspaceModelConfig.max_tokens,
                ).join(WorkspaceModelConfig, WorkspaceModelConfig.workspace_id == Workspace.id)
            )).all()
            rag_configs = (await db.execute(
                select(Workspace.code, WorkspaceRagConfig.top_k).join(
                    WorkspaceRagConfig, WorkspaceRagConfig.workspace_id == Workspace.id
                )
            )).all()

        logger.info("[chat_timing] stage=config_db_load duration=%.3fs", time.perf_counter() - started)
        return ChatConfigSnapshot(
            prompts={code: system_prompt for code, system_prompt in prompts},
            models={model_id: ModelSettings(provider, model_name)
                    for model_id, provider, model_name in models},
            model_configs={code: WorkspaceModelSettings(float(temperature), int(max_tokens))
                           for code, temperature, max_tokens in model_configs},
            top_k={code: top_k for code, top_k in rag_configs},
        )
