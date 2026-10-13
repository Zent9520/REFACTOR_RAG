from pathlib import Path
from uuid import UUID

from openai import AzureOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.not_found_exception import (
    NotFoundException,
)

from app.core.settings import (
    settings,
)

from backend.app.models.recruitment.recruitment_campaign import (
    RecruitmentCampaign,
)


class RecruitmentCVIngestService:

    @staticmethod
    async def ingest(
        db: AsyncSession,
        campaign_id: UUID,
        file_path: str,
        extraction,
    ):

        # ======================================
        # GET CAMPAIGN
        # ======================================

        query = await db.execute(

            select(
                RecruitmentCampaign,
            )

            .where(

                RecruitmentCampaign.id
                == campaign_id,

            )

        )

        campaign = (
            query
            .scalar_one_or_none()
        )

        if campaign is None:

            raise NotFoundException(
                "Recruitment campaign not found.",
            )

        # ======================================
        # EMBEDDING
        # ======================================

        client = AzureOpenAI(

            api_key=
            settings
            .AZURE_OPENAI_API_KEY,

            azure_endpoint=
            settings
            .AZURE_OPENAI_ENDPOINT,

            api_version=
            settings
            .AZURE_OPENAI_API_VERSION,

        )

        embedding_response = (

            client
            .embeddings
            .create(

                model=
                settings
                .AZURE_OPENAI_EMBEDDING_DEPLOYMENT,

                input=
                extraction.text,

            )

        )

        embedding = (

            embedding_response
            .data[0]
            .embedding

        )

        # ======================================
        # CURRENT CAMPAIGN DATA
        # ======================================

        cv_data = (
            campaign.cv_data
        )

        if cv_data is None:

            cv_data = []

        # ======================================
        # ADD THIS CV
        # ======================================

        cv_data.append(

            {

                "file_name":
                Path(file_path).name,

                "content":
                extraction.text,

                "embedding":
                embedding,

            }

        )

        # ======================================
        # SAVE
        # ======================================

        campaign.cv_data = cv_data

        await db.commit()

        await db.refresh(
            campaign
        )

        return {
            "file_name":
            Path(file_path).name,

            "embedding_dimension":
            len(embedding),

            "total_cv":
            len(cv_data),
        }