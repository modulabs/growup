from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://growup:growup_dev@localhost:5432/growup"
    N8N_LEGACY_DB_WEBHOOK_URL: str = ""
    N8N_LEGACY_DB_AUTH_USER: str = ""
    N8N_LEGACY_DB_AUTH_PASS: str = ""
    GOOGLE_CREDENTIALS_PATH: str = ""
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
