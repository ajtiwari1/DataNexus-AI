from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    app_name: str = "DataNexus AI"
    database_url: str = "postgresql://datanexus_admin:local_admin_change_me@localhost:5432/datanexus"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()



SQL_AGENT_TIMEOUT = float(
    os.getenv("SQL_AGENT_TIMEOUT", "30")
)

RAG_AGENT_TIMEOUT = float(
    os.getenv("RAG_AGENT_TIMEOUT", "30")
)

WORKFLOW_TIMEOUT = float(
    os.getenv("WORKFLOW_TIMEOUT", "60")
)

LLM_TIMEOUT = float(
    os.getenv("LLM_TIMEOUT", "20")
)
FALLBACK_ENABLED = os.getenv("FALLBACK_ENABLED", "true").lower() == "true"
