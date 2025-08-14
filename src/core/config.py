from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "mm_memory"
    vector_dim: int = 384
    embedding_provider: str = "random"  # random | sentence
    embedding_model_name: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "mm-raw"
    minio_secure: bool = False

    api_port: int = 8080

    class Config:
        env_file = ".env"


settings = Settings()


