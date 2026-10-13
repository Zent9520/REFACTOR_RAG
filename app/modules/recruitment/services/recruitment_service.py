from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.repositories.recruitment.recruitment_campaign_repository import (
    RecruitmentCampaignRepository
)

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.not_found_exception import (
    NotFoundException,
)

from backend.app.repositories.recruitment.recruitment_campaign_repository import (
    RecruitmentCampaignRepository,
)

from backend.app.repositories.ai.ai_model_repository import (
    AIModelRepository,
)

from backend.app.repositories.configuration.rag_config_repository import (
    WorkspaceConfigRepository,
)

from app.services.llm.azure_openai_service import (
    AzureOpenAIService,
)

from app.enums.prompt_code import (
    PromptCode,
)


class RecruitmentService:

    @staticmethod
    async def create_campaign(
        db: AsyncSession,
        role_id: int,
        title: str,
        job_description: str,
        created_by: UUID | None = None
    ):
        return await (
            RecruitmentCampaignRepository.create(
                db=db,
                role_id=role_id,
                title=title,
                job_description=job_description,
                created_by=created_by
            )
        )
        
   

    @staticmethod
    async def chat(
        db: AsyncSession,
        model_id: UUID,
        question: str,
        data_cv: str,
        job_description: str,
    ) -> str:

        # ======================================
        # Campaign
        # ======================================

        # campaign = await (
        #     RecruitmentCampaignRepository
        #     .get_by_id(
        #         db=db,
        #         id=campaign_id,
        #     )
        # )

        # if campaign is None:

        #     raise NotFoundException(
        #         "Recruitment campaign not found.",
        #     )

        # ======================================
        # Model
        # ======================================

        model = await (
            AIModelRepository
            .get_by_id(
                db=db,
                id=model_id,
            )
        )

        if model is None:

            raise NotFoundException(
                "AI Model not found.",
            )

        # ======================================
        # Build CV Context
        # ======================================

        # cv_data = (
        #     campaign.cv_data
        #     or {
        #         "candidates": []
        #     }
        # )

        # candidates = (
        #     cv_data
        #     .get(
        #         "candidates",
        #         []
        #     )
        # )

        # contexts = []

        # for index, candidate in enumerate(
        #     candidates,
        #     start=1,
        # ):

#             contexts.append(

#                 f"""
# Ứng viên {index}

# File:
# {candidate.get("file_name", "")}

# Nội dung CV:
# {candidate.get("content", "")}
# """

#             )

        # context = "\n\n".join(
        #     contexts
        # )

        # ======================================
        # Prompt
        # ======================================

        messages = [

            {
                "role": "system",

                "content": f"""
Bạn đang hỗ trợ người dùng phân tích
một đợt tuyển dụng.



Mô tả công việc:
{job_description}

Danh sách CV trong đợt tuyển dụng:

{data_cv}

Chỉ sử dụng thông tin được cung cấp
trong context để trả lời.

Không tự suy diễn hoặc tạo ra thông tin
không có trong các CV.
""",
            },

            {
                "role": "user",

                "content": question,
            },

        ]

        # ======================================
        # Model Config
        # ======================================

        model_config = await (
            WorkspaceConfigRepository
            .get_model_config_by_workspace_code(
                db=db,
                workspace_code=
                PromptCode.REVIEW_CV.value,
            )
        )

        temperature = float(
            model_config.temperature
        )

        max_tokens = int(
            model_config.max_tokens
        )

        # ======================================
        # Azure OpenAI
        # ======================================

        ai = AzureOpenAIService()

        answer = await ai.chat(

            model=model.model_name,

            messages=messages,

            temperature=temperature,

            max_completion_tokens=max_tokens,

        )

        return answer
    
    
    
         
    