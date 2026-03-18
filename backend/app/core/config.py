from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ArtLock - Copyright Detection API"
    VERSION: str = "1.0.0"

    # CORS Settings
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://artlockr:artlockr@localhost/artlockr_db"

    # File Storage
    UPLOAD_DIR: str = "data/uploads"
    AI_GENERATED_DIR: str = "data/ai_generated"
    FEATURES_DIR: str = "data/features"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # ML Model Settings
    MODEL_NAME: str = "resnet50"
    MODEL_WEIGHTS: str = "IMAGENET1K_V2"
    SIMILARITY_THRESHOLD: float = 0.85  # 85% similarity threshold
    BATCH_SIZE: int = 32
    DEVICE: str = "cuda"  # or "cpu"

    # Feature Extraction
    FEATURE_DIM: int = 2048  # ResNet50 feature dimension

    # API Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Gating
    ENABLE_API_GATING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.AI_GENERATED_DIR, exist_ok=True)
os.makedirs(settings.FEATURES_DIR, exist_ok=True)
