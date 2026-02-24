from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    API_NAME: str
    API_ENV: str
    API_VERSION: str

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_POOL_SIZE: int
    DB_POOL_NAME: str

    JWT_ALGORITHM: str = "HS256"

    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    CORS_ORIGINS: str
    CORS_ALLOW_CREDENTIALS: bool = True

    class Config:
        env_file = ".env"

    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

settings = Settings()
