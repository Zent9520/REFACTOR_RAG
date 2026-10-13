#----CHAT-----#
from app.modules.chat.models.conversation import *
from app.modules.chat.models.conversation_summary import *
from app.modules.chat.models.messages import *
from app.modules.chat.models.user_memories import *
#----CONFIGURATION----#
from app.modules.configuration.models.ai_model import *
from app.modules.configuration.models.ai_prompt import *
from app.modules.configuration.models.embedding_model import *
from app.modules.configuration.models.master_config import *
from app.modules.configuration.models.workspace import *
from app.modules.configuration.models.workspace_model_config import *
from app.modules.configuration.models.workspace_rag_config import *
from app.modules.configuration.models.workspace_source_config import *
#----CONTRACT----#
from app.modules.contract.models.contract_dashboard import *
from app.modules.contract.models.contract_raw import *
#----DOCUMENTS----#
from app.modules.documents.models.data_source_mode import *
from app.modules.documents.models.document_type import *
from app.modules.documents.models.sharepoint_delta_state import *
from app.modules.documents.models.sync_jobs import *
#----EXECUTIVE_DATA----#
from app.modules.executive_data.models.executive_data_dashboard import *
from app.modules.executive_data.models.executive_data_raw import *
#----IDENTITY_ACCESS----#
from app.modules.identity_access.models.department import *
from app.modules.identity_access.models.department_sensitivity_permission import *
from app.modules.identity_access.models.identity import *
from app.modules.identity_access.models.microsoft_account import *
from app.modules.identity_access.models.position_level import *
from app.modules.identity_access.models.role import *
from app.modules.identity_access.models.sensitivity_level import *
from app.modules.identity_access.models.tag import *
from app.modules.identity_access.models.tag_role_rule import *
from app.modules.identity_access.models.user_model import *
#----KNOWLEDGE_GRAPH ----#
from app.modules.knowledge_graph.models.entity import *
from app.modules.knowledge_graph.models.entity_context import *
from app.modules.knowledge_graph.models.entity_relationship import *
#----MEETING----#
from app.modules.meeting.models.meeting_analysis import *
from app.modules.meeting.models.meeting_transcript import *
#----PROJECT_TRACKING----#
from app.modules.project_tracking.models.project_tracking_dashboard import *
from app.modules.project_tracking.models.project_tracking_raw import *
#----RECRUITMENT----#
from app.modules.recruitment.models.recruitment_campaign import *
from app.modules.recruitment.models.recruitment_candidate import *
from app.modules.recruitment.models.recruitment_candidate_result import *
from app.modules.recruitment.models.review_job import *
from app.modules.recruitment.models.review_task import *