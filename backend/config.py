"""
Configuration settings for SmartRetail AI
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # API Settings
    APP_NAME = "SmartRetail AI"
    VERSION = "1.0.0"
    DEBUG = True
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/smartretail")
    # For now, keep SQLite for development
    SQLITE_DB = "inventory.db"
    
    # AI/LLM
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    LLM_MODEL = "llama-3.1-8b-instant"
    LLM_TEMPERATURE = 0
    
    # ML Models
    FORECAST_DAYS = 30
    CUSTOMER_SEGMENTS = 4
    MIN_SUPPORT = 0.01  # For market basket analysis
    MIN_CONFIDENCE = 0.2
    
    # CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8501",  # Streamlit default port
    ]

settings = Settings()
