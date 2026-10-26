from click import prompt
from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.modules.identity_access.repositories.sensitivity_repository import (
    SensitivityRepository
)

from app.modules.chat.services.prompt_builder import (
    PromptBuilder
)

from app.shared.llm.llm_factory import (
    LLMFactory
)

from app.shared.llm.azure_openai_service import (
    AzureOpenAIService,
)


class SensitivityClassifier:


    @staticmethod
    async def detect(

        db: AsyncSession,

        content: str,

        security_level:
        str | None = None,
        
        department:
        str | None = None

    ):


        levels = await (

            SensitivityRepository
            .get_all(db)

        )


        names = [

            x.code

            for x
            in levels

        ]


        prompt = (

            PromptBuilder
            .build_sensitivity_prompt(

                content=
                content,


           


                security_level=
                security_level,
                
                department=
                department

            )

        )
        
        
        
        #print("check prompt", prompt)


        llm = AzureOpenAIService()

        result = await (

    llm.generate(

        model=
        "gpt-5.1",

        prompt=
        prompt,

        temperature=
        0.2,

    
    )

)
        print("check prompt", prompt)


        return (

            result
            .strip()

            .replace(
                '"',
                ""
            )

        )