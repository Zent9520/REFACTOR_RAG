import json

from app.core.settings import (
    settings,
)

from backend.app.modules.configuration.enums.prompt_code import (
    PromptCode,
)

from backend.app.modules.configuration.repositories.ai_model_repository import (
    AIModelRepository,
)

from backend.app.modules.configuration.repositories.ai_prompt_repository import (
    AIPromptRepository,
)

from backend.app.shared.llm.azure_openai_service import (
    AzureOpenAIService,
)
from uuid import UUID

from backend.app.modules.configuration.repositories.rag_config_repository import WorkspaceConfigRepository


class ExecutiveDataAIService:

    def __init__(self):

        self.llm = AzureOpenAIService()

    async def analyze(
        self,
        db,
        report: dict,
        model_id: UUID,
    ):

        # ======================================
        # Prompt
        # ======================================

        prompt = await (

            AIPromptRepository
            .get_by_code(

                db=db,

                code=PromptCode.EXECUTIVE_DATA,

            )

        )

        if prompt is None:

            raise Exception(
                "Prompt EXECUTIVE_DATA not found."
            )

        # ======================================
        # AI Model
        # ======================================

        model = await (

            AIModelRepository
            .get_by_id(

                db=db,

                id=model_id,

            )

        )

        if model is None:

            raise Exception(
                "AI Model not found."
            )

        # ======================================
        # Build Prompt
        # ======================================

        report_json = json.dumps(

            report,

            ensure_ascii=False,

            indent=2,

        )

        system_prompt = (

            prompt.system_prompt

            .replace(

                "{{report_data}}",

                report_json,

            )

        )

        # ======================================
        # Messages
        # ======================================

        messages = [

            {

                "role": "system",

                "content": system_prompt,

            },

            {

                "role": "user",

                "content":
                "Analyze this report.",

            },

        ]

        # ======================================
        # Generate
        # ======================================
        
        workspace_code = PromptCode.EXECUTIVE_DATA.value
                
        model_config = await (
            WorkspaceConfigRepository
            .get_model_config_by_workspace_code(
        
                        db=db,
        
                        workspace_code=
                        workspace_code,
        
                    )
                )
                
        temperature = float(
                model_config.temperature
            )
        
        max_tokens = int(
                model_config.max_tokens
            )

        print("=" * 100)
        print("EXECUTIVE DATA AI ANALYSIS")
        print("=" * 100)

        answer = await (

            self.llm.chat(

                model=model.model_name,

                messages=messages,

                temperature=temperature,
                max_completion_tokens=max_tokens

            )

        )

        print("=" * 100)
        print(answer)
        print("=" * 100)

        try:

            return json.loads(
                answer,
            )

        except Exception:

            raise Exception(
                "AI did not return valid JSON."
            )