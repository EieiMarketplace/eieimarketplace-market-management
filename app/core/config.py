from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URL: str
    MONGO_DB: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    REGION_NAME: str
    S3_BUCKET_NAME: str
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
