from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central place for all environment configuration.
    Values are loaded from .env at startup - see .env.example for the full list.
    """

    database_url: str
    openai_api_key: str = ""
    gold_parquet_path: str = ""
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
