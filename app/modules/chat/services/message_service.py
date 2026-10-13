from backend.app.modules.chat.repositories.message_repository import (

 MessageRepository

)


class MessageService:


 @staticmethod

 async def create(

  db,

  payload

 ):

  return await (

   MessageRepository

   .create(

    db,

    payload

   )

  )