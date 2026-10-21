from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.core.database import (
    get_db
)

from backend.app.modules.identity_access.repositories.role_repository import (
    RoleRepository
)

from backend.app.core.settings import (
    settings
)

from backend.app.modules.chat.services.conversation_service import (
    ConversationService
)

from backend.app.modules.identity_access.repositories.permission_repository import (
    PermissionRepository
)

from backend.app.modules.chat.services.session_memory_service import (
    SessionMemoryService
)

from backend.app.modules.chat.services.query_rewrite_service import (
    QueryRewriteService
)

from backend.app.shared.azure.azure_search_service import (
    AzureSearchService
)

from backend.app.modules.chat.services.message_service import (
    MessageService
)

from backend.app.modules.chat.services.rag_service import (
    RagService
)

from backend.app.modules.chat.services.conversation_summary_service import (
    ConversationSummaryService
)


import httpx
import json


router = APIRouter(
    prefix="/bot",
    tags=["Bot"]
)


@router.post("/messages")
async def teams_message(

    body: dict,

    db: AsyncSession =
    Depends(get_db)

):

    print(
        "\n========== TEAMS ==========\n"
    )

    print(
        json.dumps(
            body,
            indent=2,
            ensure_ascii=False
        )
    )

    question = (
        body.get(
            "text",
            ""
        )
    )

    conversation_id = (
        body
        .get("conversation", {})
        .get("id")
    )

    aad_object_id = (
        body
        .get("from", {})
        .get("aadObjectId")
    )

    print(
        "question =",
        question
    )

    print(
        "conversation_id =",
        conversation_id
    )

    print(
        "aad_object_id =",
        aad_object_id
    )

    if not aad_object_id:

        print(
            "aadObjectId not found"
        )

        return {
            "status": "error"
        }

    async with httpx.AsyncClient() as client:

        # ====================
        # TOKEN
        # ====================

        token_response = await client.post(
            f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token",
            data={
                "client_id":
                settings.AZURE_CLIENT_ID,

                "client_secret":
                settings.AZURE_CLIENT_SECRET,

                "scope":
                "https://graph.microsoft.com/.default",

                "grant_type":
                "client_credentials"
            }
        )

        token_data = (
            token_response.json()
        )

        access_token = (
            token_data.get(
                "access_token"
            )
        )

        print(
            "token_ok =",
            bool(access_token)
        )

        headers = {
            "Authorization":
            f"Bearer {access_token}"
        }

        # ====================
        # USER
        # ====================

        user_response = await client.get(
            f"https://graph.microsoft.com/v1.0/users/{aad_object_id}",
            headers=headers
        )

        user_data = (
            user_response.json()
        )

        print(
            "user =",
            user_data
        )

        email = (
            user_data.get(
                "mail"
            )
            or
            user_data.get(
                "userPrincipalName"
            )
        )

        print(
            "email =",
            email
        )

        # ====================
        # GROUPS
        # ====================

        group_response = await client.get(
            f"https://graph.microsoft.com/v1.0/users/{aad_object_id}/memberOf?$select=id,displayName",
            headers=headers
        )

        group_data = (
            group_response.json()
        )

        print(
            "groups =",
            group_data
        )

        groups = (
            group_data.get(
                "value",
                []
            )
        )

        group_names = [

            group.get(
                "displayName",
                ""
            )

            for group
            in groups
        ]

        group_ids = [
            group.get("id", "")
            for group in groups
            if group.get("id")
        ]

        print(
            "group_names =",
            group_names
        )

    # ====================
    # ROLE MATCH
    # ====================

    role_names = await (
            RoleRepository
            .get_role_names(
                db=db
            )
        )

    role = next(
        (
            group
            for group
            in group_names
            if group in role_names
        ),
        None
    )

    if not role:

        return {
            "status": "error",
            "message": "role not found"
        }


    conversation = await (
        ConversationService
        .get_or_create_by_email(
            db=db,
            email=email
        )
    )

    conversation_id = str(
        conversation.id
    )

    print(
        "conversation_id =",
        conversation_id
    )


    permissions = await (
        PermissionRepository
        .get_role_access(
            db,
            role
        )
    )

    print(
        "permissions =",
        permissions
    )


    history = await (
        SessionMemoryService
        .build_context(
            db=db,
            conversation_id=conversation_id
        )
    )

    print(
        "history =",
        history
    )


    retrieval_query = await (
        QueryRewriteService
        .rewrite(
            history=history,
            question=question
        )
    )

    print(
        "retrieval_query =",
        retrieval_query
    )


    chunks = await (
        AzureSearchService
        .retrieve(
            question=question,
            group_ids=group_ids,
            permissions=permissions,
        )
    )

    print(
        "chunks =",
        chunks
    )


    await (
        MessageService
        .create(
            db,
            {
                "conversation_id":
                conversation_id,

                "role":
                "user",

                "content":
                question
            }
        )
    )


    answer = await (
        RagService()
        .ask(
            db=db,
            conversation_id=conversation_id,
            question=question,
            chunks=chunks
        )
    )

    print(
        "answer =",
        answer
    )
    
    service_url = body.get(
    "serviceUrl"
    )

    teams_conversation_id = (
        body
        .get("conversation", {})
        .get("id")
    )

    print(
        "service_url =",
        service_url
    )

    print(
        "teams_conversation_id =",
        teams_conversation_id
    )
    
    async with httpx.AsyncClient() as bot_client:

        bot_token_response = await bot_client.post(
            f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token",
            data={
                "grant_type":
                "client_credentials",

                "client_id":
                settings.BOT_APP_ID,

                "client_secret":
                settings.BOT_APP_SECRET,

                "scope":
                "https://api.botframework.com/.default"
            }
        )

        bot_access_token = (
            bot_token_response
            .json()
            .get(
                "access_token"
            )
        )
        print(
            bot_token_response.json()
        )

        reply_response = await bot_client.post(
            f"{service_url}/v3/conversations/{teams_conversation_id}/activities",
            headers={
                "Authorization":
                f"Bearer {bot_access_token}",

                "Content-Type":
                "application/json"
            },
            json={
                "type":
                "message",

                "text":
                answer
            }
        )

        print(
            "reply_status =",
            reply_response.status_code
        )

        print(
            "reply_text =",
            reply_response.text
        )

    await (
        MessageService
        .create(
            db,
            {
                "conversation_id":
                conversation_id,

                "role":
                "assistant",

                "content":
                answer
            }
        )
    )


    await (
        ConversationSummaryService
        .update_summary(
            db=db,
            conversation_id=conversation_id
        )
    )


    return {
    "type": "message",
    "text": "Hello Teams"
}
    
