from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.shared.llm.ollama_service import (
    OllamaService
)

from backend.app.modules.chat.repositories.message_repository import (
    MessageRepository
)

from backend.app.modules.chat.repositories.conversation_summary_repository import (
    ConversationSummaryRepository
)


class ConversationSummaryService:

    SUMMARY_BATCH_SIZE = 10

    @staticmethod
    async def update_summary(
        db: AsyncSession,
        conversation_id: str
    ):

        summary_record = await (
            ConversationSummaryRepository
            .get_by_conversation_id(
                db=db,
                conversation_id=conversation_id
            )
        )
        
        print("summary_record", summary_record)

        current_summary = ""
        processed_count = 0

        if summary_record:

            current_summary = (
                summary_record.summary
            )

            processed_count = (
                summary_record
                .last_processed_message_count
            )

        total_messages = await (
            MessageRepository
            .count_by_conversation(
                db=db,
                conversation_id=conversation_id
            )
        )

        new_messages_count = (
            total_messages
            - processed_count
        )

        if (
            new_messages_count
            <
            ConversationSummaryService
            .SUMMARY_BATCH_SIZE
        ):
            return None

        messages = await (
            MessageRepository
            .get_messages_after_offset(
                db=db,
                conversation_id=conversation_id,
                offset=processed_count,
                limit=ConversationSummaryService
                .SUMMARY_BATCH_SIZE
            )
        )

        conversation_text = []

        for message in messages:

            conversation_text.append(
                f"{message.role}: {message.content}"
            )

        conversation_text = "\n".join(
            conversation_text
        )

        prompt = f"""
Bạn là hệ thống quản lý bộ nhớ hội thoại.

Current Summary:

{current_summary}

New Messages:

{conversation_text}

Nhiệm vụ:

Cập nhật summary hiện tại.

Giữ lại:
- chủ đề chính
- quyết định đã thống nhất
- việc đang làm
- việc chưa hoàn thành

Loại bỏ:
- chào hỏi
- cảm ơn
- hội thoại dư thừa

Chỉ trả về summary mới.
"""

        llm = OllamaService()

        new_summary = await (
            llm.generate(
                prompt
            )
        )

        new_processed_count = (
            processed_count
            + len(messages)
        )

        if summary_record:

            await (
                ConversationSummaryRepository
                .update(
                    db=db,
                    conversation_id=conversation_id,
                    summary=new_summary,
                    last_processed_message_count=
                    new_processed_count
                )
            )

        else:

            await (
                ConversationSummaryRepository
                .create(
                    db=db,
                    conversation_id=conversation_id,
                    summary=new_summary,
                    last_processed_message_count=
                    new_processed_count
                )
            )

        return new_summary