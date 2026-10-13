from backend.app.modules.knowledge_graph.repositories.graph_repository import (
    GraphRepository
)


class GraphVisualizationService:

    @staticmethod
    async def get_graph(

        db

    ):

        return await (

            GraphRepository
            .get_graph(
                db
            )
        )