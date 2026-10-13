from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.documents.repositories.sharepoint_delta_state_repository import SharePointDeltaRepository
from backend.app.modules.documents.services.sharepoint_service import SharePointService


class DeltaService:

    @staticmethod
    async def initialize(

        db: AsyncSession,

        site_id: str,

        drive_id: str,

    ):

        state = await (
            SharePointDeltaRepository
            .get(

                db=db,

                site_id=site_id,

                drive_id=drive_id,

            )
        )

        if state:
            return

        response = await (
            SharePointService
            .get_first_delta(
                drive_id
            )
        )

        delta_link = response.get(
            "@odata.deltaLink"
        )

        if delta_link is None:

            raise Exception(
                "Cannot get delta link."
            )

        await (
            SharePointDeltaRepository
            .save(

                db=db,

                site_id=site_id,

                drive_id=drive_id,

                delta_link=delta_link,

            )
        )

    @staticmethod
    async def check(

        db: AsyncSession,

        site_id: str,

        drive_id: str,

    ):

        configuration_list = await (
            SharePointService
            .find_configuration_list(
                site_id
            )
        )

        if configuration_list is None:
            return False

        configuration = await (
            SharePointService
            .get_rag_configuration(

                site_id,

                configuration_list["id"],

            )
        )

        items = configuration.get(
            "value",
            [],
        )

        if not items:
            return False

        fields = items[0]["fields"]

        if not fields.get(
            "EnableRAG",
            False,
        ):
            return False

        state = await (
            SharePointDeltaRepository
            .get(

                db=db,

                site_id=site_id,

                drive_id=drive_id,

            )
        )

        if state is None:

            await (
                DeltaService
                .initialize(

                    db=db,

                    site_id=site_id,

                    drive_id=drive_id,

                )
            )

            return False
    
        response = await (
            SharePointService
            .get_delta(
                state.delta_link
            )
        )
        
        
        print("=" * 100)
        print("Delta Response")
        print(response)
        print("=" * 100)

        delta_link = response.get(
            "@odata.deltaLink"
        )

        if delta_link:

            await (
                SharePointDeltaRepository
                .save(

                    db=db,

                    site_id=site_id,

                    drive_id=drive_id,

                    delta_link=delta_link,

                )
            )

        return len(
            response.get(
                "value",
                [],
            )
        ) > 0