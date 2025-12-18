from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "kavak_knowledge"
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"


    DATABASE_URL: str
    REDIS_URL: str

    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_FROM: str

    RAG_TOP_K: int = 4
    HISTORY_MAX_TURNS: int = 12

settings = Settings()