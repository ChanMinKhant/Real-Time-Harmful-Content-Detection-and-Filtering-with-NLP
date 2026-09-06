"""
Configuration settings for the Harmful Content Detection NLP Backend.
Supports Development, Testing, and Production environments.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SHARED_DIR = BASE_DIR.parent / "shared"
MODELS_DIR = BASE_DIR / "models"
DEMO_DIR = BASE_DIR.parent / "demo"


class BaseConfig:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "nlpp-blur-guard-secret-key-2026")
    TESTING = False
    DEBUG = False
    
    # Server settings
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", 5000))
    
    # NLP Pipeline settings
    CACHE_SIZE = int(os.environ.get("CACHE_SIZE", 3000))
    DEFAULT_SENSITIVITY = float(os.environ.get("DEFAULT_SENSITIVITY", 0.6))
    ENABLE_TRANSFORMER = os.environ.get("NLP_TRANSFORMER", "auto").lower() not in ("off", "false", "0")
    
    # Paths
    SHARED_RULES_PATH = SHARED_DIR / "rules.json"
    MODELS_PATH = MODELS_DIR
    DEMO_FILE_PATH = DEMO_DIR / "demo.html"
    
    # CORS Origins (Chrome extension schemes, localhost variants, and null origin for file://)
    CORS_ORIGINS = [
        r"^chrome-extension://.*$",
        r"^http://localhost(:\d+)?$",
        r"^http://127\.0\.0\.1(:\d+)?$",
        "null",
    ]


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    CACHE_SIZE = 500


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str = None) -> BaseConfig:
    """Returns the appropriate config class based on env or name."""
    env = config_name or os.environ.get("FLASK_ENV", "default")
    return CONFIG_MAP.get(env.lower(), DevelopmentConfig)
