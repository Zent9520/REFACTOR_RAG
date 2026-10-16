import json

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
from backend.app.core.settings import settings
from backend.app.modules.configuration.repositories.rag_config_repository import WorkspaceConfigRepository


class ProjectTrackingAIService:

    def __init__(self):

        self.llm = AzureOpenAIService()

    async def analyze(
        self,
        db,
        project: dict,
       
    ):

        # ======================================
        # Prompt
        # ======================================

        prompt = await (
            AIPromptRepository.get_by_code(
                db=db,
                code=PromptCode.PROJECT_TRACKING    ,
            )
        )

        if prompt is None:

            raise Exception(
                "Prompt PROJECT_TRACKING not found."
            )

        # ======================================
        # AI Model
        # ======================================

        model = await (
            AIModelRepository.get_by_id(
                db=db,
                id=settings.PROJECT_TRACKING_MODEL_ID,
            )
        )

        if model is None:

            raise Exception(
                "AI Model not found."
            )

        # ======================================
        # Build Prompt
        # ======================================

        project_json = json.dumps(

            project,

            ensure_ascii=False,

            indent=2,

        )

        system_prompt = (

            prompt.system_prompt

            .replace(

                "{{project_data}}",

                project_json,

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
                "Analyze this project.",

            },

        ]

        # ======================================
        # Generate
        # ======================================

        print("=" * 100)
        print("PROJECT AI ANALYSIS")
        print("=" * 100)
        
        
        workspace_code = PromptCode.PROJECT_TRACKING.value
                                
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