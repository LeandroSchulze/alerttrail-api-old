from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List, Union, Optional

class Settings(BaseSettings):
    SECRET_KEY: str = "changeme"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./alerttrail.sqlite3"
    CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = "*"
    COOKIE_DOMAIN: Optional[str] = None  # p.ej. ".alerttrail.com" para compartir con www

    class Config:
        env_file = ".env"

settings = Settings()
