from fastapi import (

 APIRouter,

 Depends,

 HTTPException

)

from sqlalchemy.ext.asyncio import (

 AsyncSession

)

from uuid import UUID


from backend.app.core.database import (

 get_db

)


from backend.app.modules.chat.schemas.conversation_schema import (

 ConversationCreate

)


from backend.app.modules.chat.services.conversation_service import (

 ConversationService

)


from backend.app.modules.chat.repositories.message_repository import (

 MessageRepository

)

from backend.app.modules.chat.repositories.conversation_summary_repository import (

 ConversationSummaryRepository

)

router = APIRouter(
    prefix="/conversations",
    tags = ["conversations"]
    
)

#create
@router.post("/")
async def create(
    body: ConversationCreate,
    db: AsyncSession
    =
    Depends(
        get_db
    )
):
    return await (
        ConversationService.create(
            db,
            body.title,
            body.email
        )
    )

# get all by emmail

@router.get("/{email}")
async def get_all(
    email:str,
    db: AsyncSession
    =
    Depends(
        get_db
    )
):
    return await (
        ConversationService.get_all(
            db, 
            email
        )
    )
    

@router.get(

 "/{id}/messages"

)

async def get_messages(

 id:UUID,

 db:
 AsyncSession

 =

 Depends(

 get_db

 )

):

 return await (

   MessageRepository

   .get_by_conversation(

      db,

      id

   )

 )



# DELETE


@router.delete(

 "/{id}"

)

async def remove(

 id:UUID,

 db:
 AsyncSession

 =

 Depends(

 get_db

 )

):

 deleted = await (

   ConversationService

   .delete(

      db,

      id

   )

 )


 if not deleted:

  raise HTTPException(

   404,

   "Conversation not found"

  )


 return {

   "success":

   True

 }



# RENAME


@router.patch(

 "/{id}"

)

async def rename(

 id:UUID,

 title:str,

 db:
 AsyncSession

 =

 Depends(

 get_db

 )

):

 return await (

   ConversationService

   .rename(

      db,

      id,

      title

   )

 )
 
@router.get(
    "/{conversation_id}/summary"
)
async def get_summary(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    summary = await (
        ConversationSummaryRepository
        .get_by_conversation_id(
            db=db,
            conversation_id=conversation_id
        )
    )

    if not summary:

        return {
            "summary": ""
        }

    return {
        "summary": summary.summary
    }
