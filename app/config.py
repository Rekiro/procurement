from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart ERP Procurement"
    debug: bool = False

    # Database — required, no default (set in .env or deployment env vars)
    database_url: str

    # JWT — must match commercial app secret so tokens are interoperable
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480

    # MinIO / S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "smarterp-procurement"
    minio_use_ssl: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
