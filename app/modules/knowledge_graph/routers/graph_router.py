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

from backend.app.modules.knowledge_graph.services.graph_ingestion_service import (
    GraphIngestionService
)
from backend.app.modules.knowledge_graph.services.graph_visualization_service import (
    GraphVisualizationService
)

from pydantic import (
    BaseModel
)

import asyncio

from app.core.database import (
    AsyncSessionLocal
)

from backend.app.modules.knowledge_graph.services.graph_completion_service import (
    GraphCompletionService
)


router = APIRouter(
    prefix="/graph"
)


class BuildGraphRequest(
    BaseModel
):

    title: str


@router.post("/build")
async def build_graph(

    request:
    BuildGraphRequest,

    db:
    AsyncSession =
    Depends(
        get_db
    )
):

    return await (
        GraphIngestionService
        .ingest_document(

            db=db,

            title=
            request.title
        )
    )
@router.get(
    "/visualize"
)
async def visualize(

    db: AsyncSession = Depends(
        get_db
    )
):

    return await (

        GraphVisualizationService
        .get_graph(
            db
        )
    )
async def run_graph_completion():

    async with (
        AsyncSessionLocal()
    ) as db:

        try:

            await (

                GraphCompletionService
                .run(
                    db
                )

            )

            print(
                "GRAPH COMPLETION DONE"
            )

        except Exception as e:

            print(
                "GRAPH COMPLETION ERROR:",
                e
            )
            
@router.post("/completion")
async def completion():

    asyncio.create_task(

        run_graph_completion()

    )

    return {

        "status":
        "started",

        "message":
        "Graph completion is running in background"

    }