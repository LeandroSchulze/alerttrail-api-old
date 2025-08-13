from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Union

class Settings(BaseSettings):
    SECRET_KEY: str = "changeme"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./alerttrail.sqlite3"
    CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = "*"

    class Config:
        env_file = ".env"

settings = Settings()
