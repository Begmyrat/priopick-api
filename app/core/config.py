from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # AI
    OLLAMA_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.2"

    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()