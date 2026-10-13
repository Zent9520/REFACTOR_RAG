#----CHAT-----#
# ruff: noqa: F401, F403
from backend.app.modules.chat.models.conversation import *
from backend.app.modules.chat.models.conversation_summary import *
from backend.app.modules.chat.models.messages import *
from backend.app.modules.chat.models.user_memories import *
#----CONFIGURATION----#
from backend.app.modules.configuration.models.ai_model import *
from backend.app.modules.configuration.models.ai_prompt import *
from backend.app.modules.configuration.models.embedding_model import *
from backend.app.modules.configuration.models.master_config import *
from backend.app.modules.configuration.models.workspace import *
from backend.app.modules.configuration.models.workspace_model_config import *
from backend.app.modules.configuration.models.workspace_rag_config import *
from backend.app.modules.configuration.models.workspace_source_config import *
#----CONTRACT----#
from backend.app.modules.contract.models.contract_dashboard import *
from backend.app.modules.contract.models.contract_raw import *
#----DOCUMENTS----#
from backend.app.modules.documents.models.data_source_mode import *
from backend.app.modules.documents.models.document_type import *
from backend.app.modules.documents.models.sharepoint_delta_state import *
from backend.app.modules.documents.models.sync_jobs import *
#----EXECUTIVE_DATA----#
from backend.app.modules.executive_data.models.executive_data_dashboard import *
from backend.app.modules.executive_data.models.executive_data_raw import *
#----IDENTITY_ACCESS----#
from backend.app.modules.identity_access.models.department import *
from backend.app.modules.identity_access.models.department_sensitivity_permission import *
from backend.app.modules.identity_access.models.identity import *
from backend.app.modules.identity_access.models.microsoft_account import *
from backend.app.modules.identity_access.models.position_level import *
from backend.app.modules.identity_access.models.role import *
from backend.app.modules.identity_access.models.sensitivity_level import *
from backend.app.modules.identity_access.models.tag import *
from backend.app.modules.identity_access.models.tag_role_rule import *
from backend.app.modules.identity_access.models.user_model import *
#----KNOWLEDGE_GRAPH ----#
from backend.app.modules.knowledge_graph.models.entity import *
from backend.app.modules.knowledge_graph.models.entity_context import *
from backend.app.modules.knowledge_graph.models.entity_relationship import *
#----MEETING----#
from backend.app.modules.meeting.models.meeting_analysis import *
from backend.app.modules.meeting.models.meeting_transcript import *
#----PROJECT_TRACKING----#
from backend.app.modules.project_tracking.models.project_tracking_dashboard import *
from backend.app.modules.project_tracking.models.project_tracking_raw import *
#----RECRUITMENT----#
from backend.app.modules.recruitment.models.recruitment_campaign import *
from backend.app.modules.recruitment.models.recruitment_candidate import *
from backend.app.modules.recruitment.models.recruitment_candidate_result import *
from backend.app.modules.recruitment.models.review_job import *
from backend.app.modules.recruitment.models.review_task import *