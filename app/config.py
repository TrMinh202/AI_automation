from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_name: str = "historical_testcases"
    gemini_chat_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "models/text-embedding-004"
    embedding_dim: int = 768
    column_mapping_path: str = "config/column_mapping.yaml"


settings = Settings()
