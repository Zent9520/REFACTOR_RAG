from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.core.database import (
    get_db
)

from backend.app.modules.knowledge_graph.schemas.graph_chat_request import (
    GraphChatRequest
)

from backend.app.modules.knowledge_graph.services.graph_chat_service import (
    GraphChatService
)


router = APIRouter(

    prefix="/think",

    tags=["Graph Chat"]
)


@router.post("/graph")
async def graph_chat(

    body: GraphChatRequest,

    db: AsyncSession = Depends(
        get_db
    )
):

    return await (

        GraphChatService
        .ask(

            db=db,

            conversation_id=
            body.conversation_id,

            question=
            body.question
        )
    )