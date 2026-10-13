from backend.app.modules.project_tracking.services.azure_project_tracking_service import (
    AzureProjectTrackingService,
)

from backend.app.modules.project_tracking.services.project_tracking_reader_service import (
    ProjectTrackingReaderService,
)
from backend.app.modules.project_tracking.services.project_tracking_ai_service import ProjectTrackingAIService

import hashlib
import json

from datetime import (
    datetime,
    timezone,
)

from backend.app.modules.project_tracking.models.project_tracking_raw import (
    ProjectTrackingRaw,
)

from backend.app.modules.project_tracking.repositories.project_tracking_raw_repository import (
    ProjectTrackingRawRepository,
)
from backend.app.modules.project_tracking.models.project_tracking_dashboard import ProjectTrackingDashboard
from backend.app.modules.project_tracking.repositories.project_tracking_dashboard_repository import ProjectTrackingDashboardRepository



class ProjectTrackingSyncService:

    @staticmethod
    async def sync_all(db,
      
):

        print("=" * 100)
        print("PROJECT TRACKING SYNC START")
        print("=" * 100)

        #
        # Danh sách project
        #

        projects = await (
            AzureProjectTrackingService
            .get_projects()
        )

        print(
            f"TOTAL PROJECTS : {len(projects)}"
        )

        results = []

        #
        # Sync từng project
        #

        for project in projects:

            project_code = project[
                "project_code"
            ]

            print("-" * 100)
            print(
                f"SYNC PROJECT : {project_code}"
            )

            try:

                project_data = await (
                    ProjectTrackingReaderService
                    .load_project(
                        project_code=project_code,
                    )
                )
                
                
                analysis = await (
                    ProjectTrackingAIService()
                    .analyze(
                        db=db,
                        project=project_data,
                       
                    )
                )

                print("=" * 100)
                print("AI RESULT")
                print("=" * 100)
                print(analysis)
                print("=" * 100)

                #
                
                await (
                    ProjectTrackingSyncService
                    ._save_raw(
                        db=db,
                        project=project,
                        project_data=project_data,
                    )
                )

                await (
                    ProjectTrackingSyncService
                    ._save_dashboard(
                        db=db,
                        analysis=analysis,
                    )
                )

                await db.commit()
                # TODO
                # Save DB
                #

                #
                # TODO
                # AI Analyze
                #

                #
                # TODO
                # Embedding
                #

                results.append(
                    project_data
                )

                print(
                    f"SYNC SUCCESS : {project_code}"
                )

            except Exception as ex:

                print(
                    f"SYNC FAILED : {project_code}"
                )

                print(ex)

        print("=" * 100)
        print("PROJECT TRACKING SYNC END")
        print(
            f"SUCCESS : {len(results)}"
        )
        print("=" * 100)

        return results

    @staticmethod
    async def sync_project(
        db,
        project_code: str,
    ):

        print("=" * 100)
        print(
            f"SYNC PROJECT : {project_code}"
        )
        print("=" * 100)

        project_data = await (
            ProjectTrackingReaderService
            .load_project(
                project_code=project_code,
            )
        )
        
        
        analysis = await (
            ProjectTrackingAIService()
            .analyze(
                db=db,
                project=project_data,
            )
        )

        print("=" * 100)
        print("AI RESULT")
        print("=" * 100)
        print(analysis)
        print("=" * 100)

        #
        # TODO
        
        
        
        projects = await (
            AzureProjectTrackingService
            .get_projects()
        )

        project = next(

            (
                item
                for item in projects
                if item["project_code"] == project_code
            ),

            None,

        )

        if project is None:

            raise Exception(
                "Project not found."
            )

        await (
            ProjectTrackingSyncService
            ._save_raw(
                db=db,
                project=project,
                project_data=project_data,
            )
        )

        await (
            ProjectTrackingSyncService
            ._save_dashboard(
                db=db,
                analysis=analysis,
            )
        )

        await db.commit()
        # Save DB
        #

        #
        # TODO
        # AI Analyze
        #

        #
        # TODO
        # Embedding
        #

        print(
            f"SYNC SUCCESS : {project_code}"
        )

        return analysis
    
    
    @staticmethod
    async def _save_raw(
        db,
        project: dict,
        project_data: dict,
    ):
        
        
        print("in ra project", project)

        project_hash = hashlib.sha256(

            json.dumps(
                project_data,
                sort_keys=True,
                ensure_ascii=False,
            ).encode(
                "utf-8"
            )

        ).hexdigest()
        
        print("in ra project_hash", project_hash)

        item = await (
            ProjectTrackingRawRepository
            .get_by_project_code(
                db=db,
                project_code=project["project_code"],
            )
        )

        file = project["files"][0]
        
        
        last_modified = datetime.fromisoformat(
            file["last_modified"].replace(
                "Z",
                "+00:00",
            )
        )

        if item is None:

            item = ProjectTrackingRaw(

                project_code=project["project_code"],

                project_name=project_data[
                    "project"
                ][
                    "ProjectName"
                ],

                sharepoint_site_id=file[
                    "site_id"
                ],

                sharepoint_drive_id=file[
                    "drive_id"
                ],

                sharepoint_item_id=file[
                    "item_id"
                ],

                source_file=file[
                    "file_name"
                ],

                last_modified=last_modified,
                project_hash=project_hash,

                project_data=project_data,

                created_at=datetime.now(
                    timezone.utc,
                ),

                updated_at=datetime.now(
                    timezone.utc,
                ),

            )

            await (
                ProjectTrackingRawRepository
                .create(
                    db=db,
                    item=item,
                )
            )

        else:

            item.project_name = project_data[
                "project"
            ][
                "ProjectName"
            ]

            item.sharepoint_site_id = file[
                "site_id"
            ]

            item.sharepoint_drive_id = file[
                "drive_id"
            ]

            item.sharepoint_item_id = file[
                "item_id"
            ]

            item.source_file = file[
                "file_name"
            ]

            item.last_modified = last_modified

            item.project_hash = project_hash

            item.project_data = project_data

            item.updated_at = datetime.now(
                timezone.utc,
            )

            await (
                ProjectTrackingRawRepository
                .update(
                    db=db,
                    item=item,
                )
            )
            
    
    @staticmethod
    async def _save_dashboard(
        db,
        analysis: dict,
    ):
        
        print("in ra analysis", analysis)

        item = await (
            ProjectTrackingDashboardRepository
            .get_by_project_code(
                db=db,
                project_code=analysis[
                    "project_code"
                ],
            )
        )
        print("in ra item", item)

        if item is None:

            item = ProjectTrackingDashboard(

                project_code=analysis[
                    "project_code"
                ],

                summary=analysis[
                    "summary"
                ],

                overall_health_status=analysis[
                    "overall_health"
                ][
                    "status"
                ],

                overall_health_title=analysis[
                    "overall_health"
                ][
                    "title"
                ],

                progress_status=analysis[
                    "progress"
                ][
                    "status"
                ],

                progress_title=analysis[
                    "progress"
                ][
                    "title"
                ],

                budget_status=analysis[
                    "budget"
                ][
                    "status"
                ],

                budget_title=analysis[
                    "budget"
                ][
                    "title"
                ],

                risk_count=analysis[
                    "risk"
                ][
                    "count"
                ],

                risk_total=analysis[
                    "risk"
                ][
                    "total"
                ],

                task_analysis=analysis[
                    "task_analysis"
                ],

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
                ProjectTrackingDashboardRepository
                .create(
                    db=db,
                    item=item,
                )
            )

        else:

            item.summary = analysis[
                "summary"
            ]

            item.overall_health_status = analysis[
                "overall_health"
            ][
                "status"
            ]

            item.overall_health_title = analysis[
                "overall_health"
            ][
                "title"
            ]

            item.progress_status = analysis[
                "progress"
            ][
                "status"
            ]

            item.progress_title = analysis[
                "progress"
            ][
                "title"
            ]

            item.budget_status = analysis[
                "budget"
            ][
                "status"
            ]

            item.budget_title = analysis[
                "budget"
            ][
                "title"
            ]

            item.risk_count = analysis[
                "risk"
            ][
                "count"
            ]

            item.risk_total = analysis[
                "risk"
            ][
                "total"
            ]

            item.task_analysis = analysis[
                "task_analysis"
            ]

            item.analyzed_at = datetime.now(
                timezone.utc,
            )

            item.updated_at = datetime.now(
                timezone.utc,
            )

            await (
                ProjectTrackingDashboardRepository
                .update(
                    db=db,
                    item=item,
                )
            )
            
    
    
    
    
    
    