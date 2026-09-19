# Know when to remove dotenv for prod env coherence
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

class BaseConfig:
    """Shared config across environments."""
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_PORT = os.getenv("DB_PORT")

    # Apply Http Only
    JWT_SECRET             = os.getenv("JWT_SECRET", "dev_secret")
    JWT_ALGORITHM          = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TTL_MINUTES = int(os.getenv("JWT_ACCESS_TTL_MINUTES", "60"))

    # To get OAuth Provider and Credentials
    OAUTH_GOOGLE_CLIENT_ID     : str = ""
    OAUTH_GOOGLE_CLIENT_SECRET : str = ""
    OAUTH_GITHUB_CLIENT_ID     : str = ""
    OAUTH_GITHUB_CLIENT_SECRET : str = ""
    
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") 
    CORS_ORIGINS = [
        "http://localhost:8000", "http://127.0.0.1:8000", "http://192.168.0.137:8000", 
        "http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.0.137:5173"
    ]
    CSP = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' http://localhost:8000"

class StagingConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
    CORS_ORIGINS = ["https://staging.myapp.com"]
    CSP = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self' https://staging.myapp.com"

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")  # must exist in prod
    CORS_ORIGINS = ["https://myapp.com"]
    CSP = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self' https://myapp.com"

# ── Config selector ───────────────────────────────────────────────
config = {
    "development": DevelopmentConfig,
    "staging": StagingConfig,
    "production": ProductionConfig
}

def get_config():
    env = os.getenv("FASTAPI_ENV", "development")
    return config[env]()