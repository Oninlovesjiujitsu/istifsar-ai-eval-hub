import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Istifsar AI Eval Hub"
    VERSION: str = "1.0.0"
    
    # QStash
    QSTASH_CURRENT_SIGNING_KEY: str = os.getenv("QSTASH_CURRENT_SIGNING_KEY", "")
    QSTASH_NEXT_SIGNING_KEY: str = os.getenv("QSTASH_NEXT_SIGNING_KEY", "")
    
    # MLflow & DagsHub
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "")
    MLFLOW_TRACKING_USERNAME: str = os.getenv("MLFLOW_TRACKING_USERNAME", "")
    MLFLOW_TRACKING_PASSWORD: str = os.getenv("MLFLOW_TRACKING_PASSWORD", "")
    
    # Gemini API Key
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Supabase (For Phase 3)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    class Config:
        env_file = ".env"

settings = Settings()
