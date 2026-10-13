from datetime import datetime
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.documents.models.sharepoint_delta_state import SharePointDeltaState


class SharePointDeltaRepository:

    @staticmethod
    async def get(

        db: AsyncSession,

        site_id: str,

        drive_id: str,

    ):

        result = await db.execute(

            select(
                SharePointDeltaState
            ).where(

                SharePointDeltaState.site_id == site_id,

                SharePointDeltaState.drive_id == drive_id,

            )

        )

        return (
            result.scalar_one_or_none()
        )

    @staticmethod
    async def save(

        db: AsyncSession,

        site_id: str,

        drive_id: str,

        delta_link: str,

    ):

        entity = await db.get(

            SharePointDeltaState,

            {

                "site_id": site_id,

                "drive_id": drive_id,

            },

        )

        if entity is None:

            entity = SharePointDeltaState(

                site_id=site_id,

                drive_id=drive_id,

                delta_link=delta_link,

                updated_at=datetime.utcnow()

            )

            db.add(
                entity
            )

        else:

            entity.delta_link = delta_link

            entity.updated_at = datetime.utcnow()

        await db.commit()

        await db.refresh(
            entity
        )

        return entity