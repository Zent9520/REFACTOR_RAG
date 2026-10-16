from backend.app.modules.chat.repositories.message_repository import MessageRepository


class MessageService:
    @staticmethod
    async def create(db, payload, *, refresh: bool = True):
        return await MessageRepository.create(db, payload, refresh=refresh)
