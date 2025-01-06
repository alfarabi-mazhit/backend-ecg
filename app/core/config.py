from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str
    jwt_secret: str
    jwt_expires_in: int
    port: int

    class Config:
        env_file = ".env"

settings = Settings()
