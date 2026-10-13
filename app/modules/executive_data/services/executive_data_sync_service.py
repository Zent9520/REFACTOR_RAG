import hashlib
import json

from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.executive_data.models.executive_data_dashboard import (
    ExecutiveDataDashboard,
)

from backend.app.modules.executive_data.models.executive_data_raw import (
    ExecutiveDataRaw,
)

from backend.app.modules.executive_data.repositories.executive_data_repository import (
    ExecutiveDataRepository,
)

from backend.app.modules.executive_data.services.azure_executive_data_service import (
    AzureExecutiveDataService,
)

from backend.app.modules.executive_data.services.executive_data_ai_service import (
    ExecutiveDataAIService,
)

from backend.app.modules.executive_data.services.executive_data_reader_service import (
    ExecutiveDataReaderService,
)
from uuid import UUID

from backend.app.modules.configuration.enums.prompt_code import PromptCode
from backend.app.modules.configuration.repositories.ai_model_repository import AIModelRepository
from backend.app.modules.configuration.repositories.ai_prompt_repository import AIPromptRepository
from backend.app.shared.llm.azure_openai_service import AzureOpenAIService
from backend.app.modules.configuration.repositories.rag_config_repository import WorkspaceConfigRepository

class ExecutiveDataSyncService:

    @staticmethod
    async def sync_all(
        db: AsyncSession,
        model_id: UUID,
    ):
        
        
        
        exist_files = await (
            ExecutiveDataRepository
            .get_source_files(
                db=db,
            )
        )

        print("=" * 100)
        print("EXECUTIVE DATA SYNC START")
        print("=" * 100)

        datasets = await (
            AzureExecutiveDataService
            .get_datasets()
        )

        success = 0

        for dataset in datasets:
            
            
            if dataset["file_name"] in exist_files:

                print(
                    f"SKIP : {dataset['file_name']}"
                )

                continue

            try:

                print("=" * 100)
                print(dataset["file_name"])
                print("=" * 100)

                #
                # Read Excel
                #

                report = await (
                    ExecutiveDataReaderService
                    .load_dataset(
                        dataset=dataset,
                    )
                )

                #
                # AI Analyze
                #

                analysis = await (
                    ExecutiveDataAIService()
                    .analyze(
                        db=db,
                        report=report,
                         model_id=model_id,
                    )
                )

                #
                # Save Raw
                #

                raw = await (
                    ExecutiveDataSyncService
                    ._save_raw(
                        db=db,
                        dataset=dataset,
                        report=report,
                        analysis=analysis,
                    )
                )

                #
                # Save Dashboard
                #

                await (
                    ExecutiveDataSyncService
                    ._save_dashboard(
                        db=db,
                        raw=raw,
                        analysis=analysis,
                    )
                )

                await db.commit()

                success += 1

                print("SUCCESS")

            except Exception as ex:

                await db.rollback()

                print("FAILED")
                print(ex)

        print("=" * 100)
        print("EXECUTIVE DATA SYNC END")
        print(f"SUCCESS : {success}")
        print("=" * 100)

        return {

            "success": success,

            "total": len(datasets),

        }

    @staticmethod
    async def _save_raw(
        db: AsyncSession,
        dataset: dict,
        report: dict,
        analysis: dict,
    ) -> ExecutiveDataRaw:
        
        
        
        from datetime import datetime

        last_modified = None

        if dataset["last_modified"]:

            last_modified = datetime.fromisoformat(

                dataset["last_modified"]

                .replace(
                    "Z",
                    "+00:00",
                )

            )

        report_hash = hashlib.sha256(

            json.dumps(

                report,

                ensure_ascii=False,

                sort_keys=True,

            ).encode("utf-8")

        ).hexdigest()

        item = await (

            ExecutiveDataRepository
            .get_raw_by_file_hash(

                db=db,

                file_hash=report_hash,

            )

        )

        if item is None:

            item = ExecutiveDataRaw(

                dataset_name=analysis["dataset_name"],

                source_file=dataset["file_name"],

                sharepoint_site_id=dataset["site_id"],

                sharepoint_drive_id=dataset["drive_id"],

                sharepoint_item_id=dataset["item_id"],

                last_modified=last_modified,

                file_hash=report_hash,

                report_data=report,

                created_at=datetime.now(
                    timezone.utc,
                ),

                updated_at=datetime.now(
                    timezone.utc,
                ),

            )

            await (

                ExecutiveDataRepository
                .create_raw(

                    db=db,

                    item=item,

                )

            )

            await db.flush()

        else:

            item.dataset_name = analysis["dataset_name"]

            item.source_file = dataset["file_name"]

            item.sharepoint_site_id = dataset["site_id"]

            item.sharepoint_drive_id = dataset["drive_id"]

            item.sharepoint_item_id = dataset["item_id"]

            item.last_modified = last_modified

            item.file_hash = report_hash

            item.report_data = report

            item.updated_at = datetime.now(
                timezone.utc,
            )

            await (

                ExecutiveDataRepository
                .update_raw(

                    db=db,

                    item=item,

                )

            )

        return item

    @staticmethod
    async def _save_dashboard(
        db: AsyncSession,
        raw: ExecutiveDataRaw,
        analysis: dict,
    ):

        dashboard = await (

            ExecutiveDataRepository
            .get_dashboard_by_dataset_id(

                db=db,

                dataset_id=raw.id,

            )

        )

        if dashboard is None:

            dashboard = ExecutiveDataDashboard(

                dataset_id=raw.id,

                summary=analysis["summary"],

                analyzed_at=datetime.now(
                    timezone.utc,
                ),

                created_at=datetime.now(
                    timezone.utc,
                ),

                updated_at=datetime.now(
                    timezone.utc,
                ),

            )

            await (

                ExecutiveDataRepository
                .create_dashboard(

                    db=db,

                    item=dashboard,

                )

            )

        else:

            dashboard.summary = analysis["summary"]

            dashboard.analyzed_at = datetime.now(
                timezone.utc,
            )

            dashboard.updated_at = datetime.now(
                timezone.utc,
            )

            await (

                ExecutiveDataRepository
                .update_dashboard(

                    db=db,

                    item=dashboard,

                )

            )
            
    
    
    @staticmethod
    async def chat(
        db: AsyncSession,
        question: str,
        model_id: UUID,
    ):

        #
        # AI Model
        #

        model = await (
            AIModelRepository
            .get_by_id(
                db=db,
                id=model_id,
            )
        )

        #
        # Prompt Detection
        #

        detection_prompt = await (
            AIPromptRepository
            .get_by_code(
                db=db,
                code=PromptCode.EXECUTIVE_DATA_DETECTION,
            )
        )

        #
        # Dataset Summary
        #

        datasets = await (
            ExecutiveDataRepository
            .get_dataset_summaries(
                db=db,
            )
        )

        dataset_text = "\n".join(

            f'- ID: {item["id"]}\n'
            f'  Name: {item["dataset_name"]}\n'
            f'  Summary: {item["summary"]}\n'

            for item in datasets

        )

        #
        # Build Detection Prompt
        #

        prompt = (

            detection_prompt.system_prompt

            .replace(
                "{{datasets}}",
                dataset_text,
            )

            .replace(
                "{{question}}",
                question,
            )

        )

        #
        # Detection
        #

        result = await (

            AzureOpenAIService()

            .generate(

                model=model.model_name,

                prompt=prompt,

                temperature=0.2,

            )

        )

        detect = json.loads(result)

        #
        # Load Context
        #

        contexts = await (

            ExecutiveDataRepository
            .get_report_data_list(

                db=db,

                dataset_ids=[
                    UUID(id)
                    for id in detect["dataset_ids"]
                ],

            )

        )

        #
        # Chat Prompt
        #

        chat_prompt = await (

            AIPromptRepository
            .get_by_code(

                db=db,

                code=PromptCode.EXECUTIVE_DATA_CHAT,

            )

        )

        #
        # Messages
        #

        messages = [

            {

                "role": "system",

                "content": chat_prompt.system_prompt,

            },

            {

                "role": "user",

                "content":

    f"""
    Câu hỏi:

    {question}

    ==================================================

    Dữ liệu:

    {json.dumps(
        contexts,
        ensure_ascii=False,
        indent=2,
    )}
    """,

            },

        ]

        #
        # Chat
        #
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
        

        answer = await (

            AzureOpenAIService()

            .chat(

                model=model.model_name,

                messages=messages,

                temperature=temperature,
                max_completion_tokens=max_tokens

            )

        )

        return {

            "answer": answer,

        }
        
        