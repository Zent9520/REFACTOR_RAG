from fastapi import (APIRouter, Depends, HTTPException)

from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import (AsyncSession)

from backend.app.core.database import (get_db)

from uuid import uuid4

from backend.app.modules.chat.schemas.chat_schema import (ChatRequest,)

from backend.app.shared.azure.azure_search_service import (AzureSearchService)

from backend.app.modules.chat.services.rag_service import (RagService)

from backend.app.modules.configuration.enums.prompt_code import (PromptCode)

import json
import asyncio
import logging
import time

from backend.app.modules.configuration.chat_config_cache import ChatConfigCache

from backend.app.modules.identity_access.services.permission_service import (
    PermissionService,
)
from backend.app.shared.resilience.capacity_manager import capacity_manager
from backend.app.shared.resilience.exceptions import (
    CapacityError,
    PipelineCapacityExceededError,
    UserCapacityExceededError,
)

logger = logging.getLogger("uvicorn.error")


async def _get_access_permissions(
    db: AsyncSession,
    body: ChatRequest,
) -> list[dict]:
    if not any(
        str(group_id).strip()
        for group_id in body.group_ids
    ):
        raise HTTPException(
            status_code=403,
            detail="User does not belong to an allowed group.",
        )

    role_name = body.role.strip()

    if not role_name:
        raise HTTPException(
            status_code=403,
            detail="Role is required for document access.",
        )

    permissions = await PermissionService.get_role_access(
        db=db,
        role_name=role_name,
    )

    if not permissions:
        raise HTTPException(
            status_code=403,
            detail="Role does not have document access permission.",
        )

    return permissions


async def _chat_admission(body: ChatRequest):
    try:
        permit = await capacity_manager.acquire_admission(
            user_id=body.microsoft_object_id,
        )
    except UserCapacityExceededError as exc:
        raise HTTPException(
            status_code=429,
            detail="Bạn đang có quá nhiều yêu cầu đang xử lý.",
            headers={"Retry-After": "10"},
        ) from exc
    except PipelineCapacityExceededError as exc:
        raise HTTPException(
            status_code=503,
            detail="Hệ thống đang xử lý nhiều yêu cầu. Vui lòng thử lại sau.",
            headers={"Retry-After": "10"},
        ) from exc

    try:
        yield permit
    finally:
        await permit.release()


router = APIRouter(
    prefix=
    "/chat",
    tags=
    ["Chat"],
    dependencies=[Depends(_chat_admission)],

)

def sse_event(
    event: str,
    data,
) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
    )


def build_internal_sources(
    chunks: list,
) -> list:
    
    source_map = {}

    for chunk in chunks:

        file = chunk["source_file"]

        if file not in source_map:

            source_map[file] = {
                "source_file": file,
                "source_url": chunk["source_url"],
                "drive_id": chunk.get("drive_id"),
                "drive_item_id": chunk.get("drive_item_id"),
                "excerpt": chunk["content"],
                "type": "internal",
            }

    return list(source_map.values())


class PublicAnswerStreamParser:

    def __init__(self):

        self._buffer = ""
        self._position = 0
        self._started = False
        self._finished = False
        self._escaped = False
        self._unicode_escape = ""

    def feed(
        self,
        token: str,
    ) -> str:

        self._buffer += token
        delta = []

        while self._position < len(self._buffer):

            char = self._buffer[self._position]

            if not self._started:

                key_position = self._buffer.find(
                    '"answer"',
                    self._position,
                )

                if key_position < 0:
                    self._position = max(
                        0,
                        len(self._buffer) - len('"answer"'),
                    )
                    break

                colon_position = self._buffer.find(
                    ":",
                    key_position + len('"answer"'),
                )

                if colon_position < 0:
                    self._position = key_position
                    break

                quote_position = self._buffer.find(
                    '"',
                    colon_position + 1,
                )

                if quote_position < 0:
                    self._position = key_position
                    break

                self._position = quote_position + 1
                self._started = True
                continue

            if self._finished:
                break

            if self._unicode_escape:

                needed = 4 - len(self._unicode_escape)
                self._unicode_escape += self._buffer[
                    self._position:self._position + needed
                ]
                self._position += min(
                    needed,
                    len(self._buffer) - self._position,
                )

                if len(self._unicode_escape) < 4:
                    break

                delta.append(
                    chr(
                        int(
                            self._unicode_escape,
                            16,
                        )
                    )
                )
                self._unicode_escape = ""
                self._escaped = False
                continue

            if self._escaped:

                escape_map = {
                    '"': '"',
                    "\\": "\\",
                    "/": "/",
                    "b": "\b",
                    "f": "\f",
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                }

                if char == "u":
                    self._unicode_escape = ""
                else:
                    delta.append(
                        escape_map.get(
                            char,
                            char,
                        )
                    )
                    self._escaped = False

                self._position += 1
                continue

            if char == "\\":
                self._escaped = True
                self._position += 1
                continue

            if char == '"':
                self._finished = True
                self._position += 1
                break

            delta.append(char)
            self._position += 1

        return "".join(delta)


def parse_public_answer(
    raw_answer: str,
    streamed_answer: str,
) -> tuple[str, list]:

    try:

        result = json.loads(raw_answer)

        return (
            result["answer"],
            result["sources"],
        )

    except json.JSONDecodeError:

        return (
            streamed_answer or raw_answer,
            [],
        )


async def _prepare_chat_request(
    db: AsyncSession,
    body: ChatRequest,
    request_started: float,
    *,
    helpdesk: bool,
) -> list:
    route = "helpdesk" if helpdesk else "query"

    chunks = []
    if body.mode != PromptCode.PUBLIC:
        permissions = await _get_access_permissions(db=db, body=body)
        # Permission data is now plain dictionaries; release the read transaction
        # before waiting on Azure Search and the LLM stream.
        await db.rollback()
        if helpdesk:
            top_k = await ChatConfigCache.lookup(
                "top_k", PromptCode.HELPDESK.value,
            )
            chunks = await AzureSearchService.retrieve_helpdesk(
                question=body.question,
                top_k=top_k,
                group_ids=body.group_ids,
                permissions=permissions,
            )
        else:
            chunks = await AzureSearchService.retrieve(
                question=body.question,
                rewrite_query=False,
                group_ids=body.group_ids,
                permissions=permissions,
            )
    logger.info(
        "[chat_timing] route=%s stage=retrieval elapsed=%.3fs chunks=%d",
        route, time.perf_counter() - request_started, len(chunks),
    )

    return chunks


async def _rollback_chat_db(db: AsyncSession) -> None:
    try:
        await db.rollback()
    except Exception:
        logger.exception("Chat DB rollback failed")


async def _stream_chat_response(
    db: AsyncSession,
    body: ChatRequest,
    request_started: float,
    *,
    helpdesk: bool,
):
    route = "helpdesk" if helpdesk else "query"
    title = str(body.question)
    conversation_id = str(body.conversation_id)

    logger.info(
        "[chat_timing] route=%s stage=first_sse elapsed=%.3fs db_tx_open=%s",
        route, time.perf_counter() - request_started, db.in_transaction(),
    )
    yield sse_event(
        "metadata",
        {"conversation_id": conversation_id, "title": title, "sources": None},
    )

    try:
        chunks = await _prepare_chat_request(
            db, body, request_started, helpdesk=helpdesk,
        )
        sources = (
            None if body.mode == PromptCode.PUBLIC
            else build_internal_sources(chunks)
        )
        if body.mode != PromptCode.PUBLIC:
            yield sse_event(
                "metadata",
                {
                    "conversation_id": conversation_id,
                    "title": title,
                    "sources": sources,
                },
            )

        rag_service = RagService()
        workspace_code = (
            PromptCode.HELPDESK.value
            if helpdesk else PromptCode.CHAT_RAG.value
        )
        public_parser = (
            PublicAnswerStreamParser()
            if body.mode == PromptCode.PUBLIC else None
        )
        raw_answer = ""
        full_answer = ""
        llm_started = time.perf_counter()
        first_model_token = True
        first_answer_sse = True
        async for token in rag_service.ask_stream(
            db=db,
            conversation_id=body.conversation_id,
            question=body.question,
            chunks=chunks,
            model_id=body.model_id,
            mode=body.mode,
            workspace_code=workspace_code,
            history="",
            trace_id=conversation_id,
        ):
            if first_model_token:
                logger.info(
                    "[chat_timing] route=%s stage=first_model_token llm=%.3fs elapsed=%.3fs",
                    route, time.perf_counter() - llm_started,
                    time.perf_counter() - request_started,
                )
                first_model_token = False
            raw_answer += token
            answer_delta = (
                public_parser.feed(token)
                if public_parser is not None else token
            )
            if answer_delta:
                if first_answer_sse:
                    logger.info(
                        "[chat_timing] route=%s stage=first_answer_sse elapsed=%.3fs",
                        route, time.perf_counter() - request_started,
                    )
                    first_answer_sse = False
                full_answer += answer_delta
                yield sse_event("answer", {"delta": answer_delta})

        logger.info(
            "[chat_timing] route=%s stage=generation_done llm=%.3fs elapsed=%.3fs",
            route, time.perf_counter() - llm_started,
            time.perf_counter() - request_started,
        )

        if body.mode == PromptCode.PUBLIC:
            full_answer, sources = parse_public_answer(
                raw_answer=raw_answer,
                streamed_answer=full_answer,
            )
            yield sse_event(
                "metadata",
                {
                    "conversation_id": conversation_id,
                    "title": title,
                    "sources": sources,
                },
            )

        logger.info(
            "[chat_timing] route=%s stage=done_sse elapsed=%.3fs",
            route, time.perf_counter() - request_started,
        )
        yield sse_event(
            "done",
            {
                "conversation_id": conversation_id,
                "title": title,
                "answer": full_answer,
                "sources": sources,
            },
        )
    except asyncio.CancelledError:
        await _rollback_chat_db(db)
        raise
    except HTTPException as exc:
        await _rollback_chat_db(db)
        logger.warning("Chat access error: %s", exc.detail)
        yield sse_event(
            "error",
            {"code": "ACCESS_DENIED", "message": str(exc.detail)},
        )
    except CapacityError as exc:
        await _rollback_chat_db(db)
        logger.warning("Chat stream capacity error: %s", exc)
        yield sse_event(
            "error",
            {
                "code": "LLM_BUSY",
                "message": "Hệ thống đang xử lý nhiều yêu cầu. Vui lòng thử lại sau.",
            },
        )
    except Exception:
        await _rollback_chat_db(db)
        logger.exception("Chat stream failed route=%s", route)
        yield sse_event(
            "error",
            {
                "code": "CHAT_FAILED",
                "message": "Không thể hoàn thành yêu cầu. Vui lòng thử lại.",
            },
        )


@router.post("/query")
async def query(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    request_started = time.perf_counter()
    if body.conversation_id is None:
        body.conversation_id = uuid4()
    logger.info(
        "[chat_timing] route=query stage=response_ready elapsed=%.3fs",
        time.perf_counter() - request_started,
    )
    return StreamingResponse(
        _stream_chat_response(db, body, request_started, helpdesk=False),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/helpdesk")
async def helpdesk_query(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    request_started = time.perf_counter()
    if body.conversation_id is None:
        body.conversation_id = uuid4()
    logger.info(
        "[chat_timing] route=helpdesk stage=response_ready elapsed=%.3fs",
        time.perf_counter() - request_started,
    )
    return StreamingResponse(
        _stream_chat_response(db, body, request_started, helpdesk=True),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
