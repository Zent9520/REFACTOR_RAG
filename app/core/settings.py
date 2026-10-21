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

    # Single-process PoC backpressure. Use a distributed limiter when the
    # application runs with multiple workers or containers.
    RAG_MAX_IN_FLIGHT_REQUESTS: int = 100
    RAG_USER_MAX_CONCURRENCY: int = 2
    RAG_USER_REQUESTS_PER_MINUTE: int = 10
    RAG_ADMISSION_TIMEOUT_SECONDS: float = 0.1
    RAG_MAX_HISTORY_CHARS: int = 12000
    RAG_MAX_CONTEXT_CHARS: int = 30000
    RAG_MAX_OUTPUT_TOKENS: int = 2000

    AZURE_SEARCH_MAX_CONCURRENCY: int = 8
    AZURE_SEARCH_QUEUE_TIMEOUT_SECONDS: float = 20.0
    AZURE_SEARCH_REQUEST_TIMEOUT_SECONDS: float = 15.0

    AZURE_OPENAI_CHAT_MAX_CONCURRENCY: int = 6
    AZURE_OPENAI_CHAT_QUEUE_TIMEOUT_SECONDS: float = 30.0
    AZURE_OPENAI_CHAT_REQUEST_TIMEOUT_SECONDS: float = 90.0
    AZURE_OPENAI_EMBEDDING_MAX_CONCURRENCY: int = 8
    AZURE_OPENAI_EMBEDDING_QUEUE_TIMEOUT_SECONDS: float = 20.0
    AZURE_OPENAI_EMBEDDING_REQUEST_TIMEOUT_SECONDS: float = 20.0
    AZURE_OPENAI_GENERATE_MAX_TOKENS: int = 1000

    AZURE_OPENAI_RPM_LIMIT: int = 60
    AZURE_OPENAI_TPM_LIMIT: int = 100000
    AZURE_OPENAI_QUOTA_SAFETY_RATIO: float = 0.85
    AZURE_OPENAI_QUOTA_QUEUE_TIMEOUT_SECONDS: float = 30.0

    AZURE_RETRY_MAX_ATTEMPTS: int = 3
    AZURE_RETRY_BASE_DELAY_SECONDS: float = 1.0
    AZURE_RETRY_MAX_DELAY_SECONDS: float = 10.0
    AZURE_RETRY_JITTER_SECONDS: float = 0.5

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore",
    )


settings = Settings()
