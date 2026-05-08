from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "order-service"
    database_url: str = "postgresql+asyncpg://orders:orders@order-db:5432/order_db"
    catalog_service_url: str = "http://catalog-service:8000"
    internal_service_token: str = "internal-service-token"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
