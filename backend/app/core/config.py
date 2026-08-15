from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniAI Personal Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/omniai"
    
    # Supabase (Optional for local development)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # ChromaDB (Memory)
    CHROMA_PATH: str = "./chroma_db"
    
    # AI Models
    OLLAMA_HOST: str = "http://localhost:11434"
    # A smaller/faster model for snappy conversational replies. llama3.1 (8B)
    # is noticeably slower on typical consumer hardware; llama3.2:3b trades a
    # bit of quality for much lower latency. Run `ollama pull llama3.2:3b`,
    # or override via the .env file / Settings page if you'd rather use
    # something else (e.g. a bigger model if you have the GPU for it).
    DEFAULT_MODEL: str = "llama3.2:3b"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

settings = Settings()
