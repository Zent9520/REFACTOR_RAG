from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.chat.services.prompt_builder import (
    PromptBuilder
)

from backend.app.shared.llm.llm_factory import (
    LLMFactory
)

from backend.app.shared.llm.response_parser import (
    ResponseParser
)

from backend.app.modules.identity_access.repositories.tag_repository import (
    TagRepository
)

from backend.app.modules.identity_access.repositories.role_repository import (
    RoleRepository
)


class SemanticTagger:

    @staticmethod
    async def detect_tags(
        db: AsyncSession,
        content: str
    ):

        allowed_tags = await TagRepository.get_all(
            db
        )

        available_roles = await RoleRepository.get_all(
            db
        )

        prompt = PromptBuilder.build_semantic_tag_prompt(
            content=content,
            tags=allowed_tags,
            roles=available_roles,
        )

        llm = LLMFactory.get_llm()

        raw_response = await llm.generate(
            prompt
        )

        tags = ResponseParser.parse_json_array(
            raw_response
        )

        return tags