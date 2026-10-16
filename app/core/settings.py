import pathlib
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from uuid import UUID

ENV_FILE = pathlib.Path(__file__).resolve().parents[2] / ".env"



class Settings(BaseSettings):
    CHAT_REWRITE_DEPLOYMENT: str = "gpt-5.1"
    CHAT_REWRITE_TIMEOUT_SECONDS: float = 4.0


    DATABASE_URL: str | None = None
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    SECRET_KEY: str | None = None
    ALGORITHM: str | None = None

    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = None

    LLM_PROVIDER: str | None = None

    LOCAL_MODEL_URL: str | None = None

    LOCAL_MODEL_NAME: str | None = None


    # ===== thêm =====
    
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""

    AZURE_SEARCH_ENDPOINT: str | None = None

    AZURE_SEARCH_INDEX: str | None = None

    AZURE_SEARCH_KEY: str | None = None
    
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    
   
    GOOGLE_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    
    BOT_APP_ID: str = ""
    BOT_APP_SECRET: str = ""
    
    
    OLLAMA_MODEL: str = "gemma3:1b"
    
    SHAREPOINT_SITE_ID: str = ""
    SHAREPOINT_DRIVE_ID: str =""
    
    LOGIC_APP_URL: str 
    
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    # BGE is optional until the legal embedding endpoint is deployed.
    BGE_EMBEDDING_ENDPOINT: str | None = None
    BGE_EMBEDDING_API_KEY: str | None = None
    BGE_EMBEDDING_MODEL: str | None = "BAAI/bge-m3"
    BGE_EMBEDDING_REQUEST_FORMAT: str | None = "openai"
    BGE_QUERY_PREFIX: str | None = ""
    BGE_NORMALIZE_EMBEDDINGS: bool = True
    MICROSOFT_REDIRECT_URI: str
    BGE_LOCAL_MODEL_PATH: str | None = None   # vd: "models/bge-m3"
    BGE_USE_FP16: bool = False                # True nếu máy có GPU
    
    MAX_FILE_REVIEW: int = 5
    MIN: int = 0
    
    
    PROJECT_TRACKING_SITE_NAME: str

    PROJECT_TRACKING_LIBRARY_NAME: str
    
    EXECUTIVE_DATA_SITE_NAME: str



    EXECUTIVE_DATA_LIBRARY_NAME: str
    
    
   
    
    PROJECT_TRACKING_MODEL_ID: UUID 
    
    EXECUTIVE_DATA_MODEL_ID: UUID
    
    
    
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str

    LEGAL_DB_PATH: str = str(
        pathlib.Path(__file__).resolve().parents[1]
        / "modules" / "data" / "legal_vbpl.duckdb"
    )
    
    
    GOOGLE_CUSTOMER_ID: str
    GOOGLE_CUSTOMER_SECRET: str


    GOOGLE_REDIRECT_URI: str
    
    MEETING_SYNC_USER_ID: str

    AZURE_SEARCH_CONTRACT_NAME: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore",
    )


settings = Settings()
