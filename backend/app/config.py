from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"

    # Prospect research
    apollo_api_key: str = ""
    tavily_api_key: str = ""

    # Email — Gmail SMTP
    gmail_user: str = ""
    gmail_app_password: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./sdr_agent.db"

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


settings = Settings()
