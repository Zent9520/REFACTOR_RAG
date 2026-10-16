from fastapi import (APIRouter, Depends)

from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import (AsyncSession)

from backend.app.core.database import (get_db)

from uuid import uuid4

from backend.app.modules.chat.schemas.chat_schema import (ChatRequest,)

from backend.app.shared.azure.azure_search_service import (AzureSearchService)

from backend.app.modules.chat.services.rag_service import (RagService)

from backend.app.modules.chat.services.message_service import (MessageService)

from backend.app.modules.chat.services.session_memory_service import (SessionMemoryService)

from backend.app.modules.chat.services.query_rewrite_service import (QueryRewriteService)

from backend.app.modules.chat.services.conversation_service import (ConversationService)

from backend.app.modules.chat.repositories.conversation_repository import (ConversationRepository)

from backend.app.modules.configuration.enums.prompt_code import (PromptCode)

import json
import asyncio
import logging

from backend.app.modules.configuration.repositories.rag_config_repository import WorkspaceConfigRepository

logger = logging.getLogger(__name__)


async def _build_retrieval_query(db, body: ChatRequest) -> str:
    if body.mode == PromptCode.PUBLIC:
        return body.question

    history = await SessionMemoryService.build_context(
        db=db,
        conversation_id=body.conversation_id,
    )
    if not history:
        return body.question

    return await QueryRewriteService.rewrite(history=history, question=body.question)


router = APIRouter(
    prefix=
    "/chat",
    tags=
    ["Chat"]

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


@router.post(

 "/query"

)

async def query(

 body:ChatRequest,

 db:AsyncSession

 =

 Depends(

  get_db

 )

):


 if body.conversation_id is None:
    body.conversation_id = uuid4()

 conversation = await ConversationRepository.get_by_id(
        db=db,
        conversation_id=body.conversation_id,
    )

 if conversation is None:
    await ConversationService.create(
        db=db,
        conversation_id=body.conversation_id,
        title=body.question,
        email=None,
    )

#  retrieval_query = await (
#      SessionMemoryService
#      .build_retrieval_query(
#          db=db,
#          conversation_id=body.conversation_id,
#          question = body.question
#      )
#  )



 retrieval_query = await _build_retrieval_query(db, body)
 
#  print("in ra retrieval", retrieval_query)
 chunks = []
 if body.mode != PromptCode.PUBLIC:

    chunks = await AzureSearchService.retrieve(
        question=retrieval_query,
        rewrite_query=False,
        user_object_id=body.microsoft_object_id,
        group_ids=body.group_ids,
    )



 


 # =======

 # SAVE USER

 # =======

 await (

  MessageService

  .create(

   db,

   {

    "conversation_id":

    body.conversation_id,

    "role":

    "user",

    "content":

    body.question

   },
   refresh=False,

  )

 )


 rag_service = (

  RagService()

 )
 
 workscpace_code = PromptCode.CHAT_RAG.value


 sources = (
    None
    if body.mode == PromptCode.PUBLIC
    else build_internal_sources(chunks)
 )

 async def stream_response():

    raw_answer = ""
    full_answer = ""
    final_sources = sources
    public_parser = (
        PublicAnswerStreamParser()
        if body.mode == PromptCode.PUBLIC
        else None
    )

    yield sse_event(
        "metadata",
        {
            "conversation_id": str(body.conversation_id),
            "title": str(body.question),
            "sources": final_sources,
        },
    )

    async for token in rag_service.ask_stream(
        db=db,
        conversation_id=body.conversation_id,
        question=body.question,
        chunks=chunks,
        model_id=body.model_id,
        mode=body.mode,
        workspace_code=workscpace_code,
    ):

        raw_answer += token

        answer_delta = token

        if public_parser is not None:

            answer_delta = public_parser.feed(token)

        if answer_delta:

            full_answer += answer_delta

            yield sse_event(
                "answer",
                {
                    "delta": answer_delta,
                },
            )

    if body.mode == PromptCode.PUBLIC:

        full_answer, final_sources = parse_public_answer(
            raw_answer=raw_answer,
            streamed_answer=full_answer,
        )

        yield sse_event(
            "metadata",
            {
                "conversation_id": str(body.conversation_id),
                "title": str(body.question),
                "sources": final_sources,
            },
        )

    await (
        MessageService
        .create(
            db,
            {
                "conversation_id": body.conversation_id,
                "role": "assistant",
                "content": full_answer,
            },
            refresh=False,
        )
    )

    yield sse_event(
        "done",
        {
            "conversation_id": str(body.conversation_id),
            "title": str(body.question),
            "answer": full_answer,
            "sources": final_sources,
        },
    )

 return StreamingResponse(
    stream_response(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    },
)
 
 
@router.post("/helpdesk")
async def helpdesk_query(

    body: ChatRequest,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    if body.conversation_id is None:

        body.conversation_id = uuid4()

    conversation = await (
        ConversationRepository.get_by_id(
            db=db,
            conversation_id=body.conversation_id,
        )
    )

    if conversation is None:

        await ConversationService.create(
            db=db,
            conversation_id=body.conversation_id,
            title=body.question,
            email=None,
        )

    retrieval_query = await _build_retrieval_query(db, body)

    # ======================================
    # HELPDESK RETRIEVAL
    # ======================================
    
    top_k = await (
    WorkspaceConfigRepository
    .get_top_k_by_workspace_code(

        db=db,

        workspace_code=
        PromptCode.HELPDESK.value,

    )
)

    chunks = []

    if body.mode != PromptCode.PUBLIC:

        chunks = AzureSearchService.retrieve_helpdesk(
            question=retrieval_query,
            top_k=top_k,
            user_object_id=body.microsoft_object_id,
            group_ids=body.group_ids,
        )

    # ======================================
    # SAVE USER
    # ======================================

    await (

        MessageService
        .create(

            db,

            {

                "conversation_id":
                body.conversation_id,

                "role":
                "user",

                "content":
                body.question,

            },
            refresh=False,

        )

    )

    rag_service = RagService()
    
    
    workscpace_code = PromptCode.HELPDESK.value

    sources = (
        None
        if body.mode == PromptCode.PUBLIC
        else build_internal_sources(chunks)
    )

    async def stream_response():

        raw_answer = ""
        full_answer = ""
        final_sources = sources
        public_parser = (
            PublicAnswerStreamParser()
            if body.mode == PromptCode.PUBLIC
            else None
        )

        yield sse_event(
            "metadata",
            {
                "conversation_id": str(body.conversation_id),
                "title": body.question,
                "sources": final_sources,
            },
        )

        async for token in rag_service.ask_stream(
            db=db,
            conversation_id=body.conversation_id,
            question=body.question,
            chunks=chunks,
            model_id=body.model_id,
            mode=body.mode,
            workspace_code=workscpace_code,
        ):

            raw_answer += token

            answer_delta = token

            if public_parser is not None:

                answer_delta = public_parser.feed(token)

            if answer_delta:

                full_answer += answer_delta

                yield sse_event(
                    "answer",
                    {
                        "delta": answer_delta,
                    },
                )

        if body.mode == PromptCode.PUBLIC:

            full_answer, final_sources = parse_public_answer(
                raw_answer=raw_answer,
                streamed_answer=full_answer,
            )

            yield sse_event(
                "metadata",
                {
                    "conversation_id": str(body.conversation_id),
                    "title": body.question,
                    "sources": final_sources,
                },
            )

        await (
            MessageService
            .create(
                db,
                {
                    "conversation_id": body.conversation_id,
                    "role": "assistant",
                    "content": full_answer,
                },
                refresh=False,
            )
        )

        yield sse_event(
            "done",
            {
                "conversation_id": str(body.conversation_id),
                "title": body.question,
                "answer": full_answer,
                "sources": final_sources,
            },
        )

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
