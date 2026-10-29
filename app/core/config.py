from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "DataNexus AI"
    database_url: str = "postgresql://datanexus_admin:local_admin_change_me@localhost:5432/datanexus"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
