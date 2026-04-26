from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "catalog-service"
    database_url: str = "postgresql+asyncpg://catalog:catalog@catalog-db:5432/catalog_db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
