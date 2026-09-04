from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central place for all environment configuration.
    Values are loaded from .env at startup - see .env.example for the full list.
    """

    database_url: str
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    copilot_max_rows: int = 200
    copilot_query_timeout_seconds: float = 10.0
    gold_parquet_path: str = ""
    allowed_origins: str = "http://localhost:3001"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()