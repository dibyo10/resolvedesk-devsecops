from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ResolveDesk API"
    database_url: str = (
        "postgresql+psycopg://resolvedesk:resolvedesk@localhost:5432/resolvedesk"
    )
    cors_origins: list[str] = ["http://localhost:8080"]
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
