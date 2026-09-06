"""
Harmful Content Blur Guard Flask Application Factory.
"""

import time
from typing import Optional, Type, Union
from flask import Flask
from flask_cors import CORS

from app.config import BaseConfig, get_config
from app.routes.api import api_bp
from app.routes.views import views_bp
from pipeline import CascadingNLPPipeline


def create_app(config_target: Optional[Union[str, Type[BaseConfig]]] = None) -> Flask:
    """
    Creates and configures a Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    if isinstance(config_target, str) or config_target is None:
        config_class = get_config(config_target)
    else:
        config_class = config_target
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["*"])}})

    # Record startup timestamp
    app.config["START_TIME"] = time.time()

    # Initialize global NLP Pipeline
    cache_size = app.config.get("CACHE_SIZE", 3000)
    enable_transformer = app.config.get("ENABLE_TRANSFORMER", True)
    app.nlp_pipeline = CascadingNLPPipeline(cache_size=cache_size, enable_transformer=enable_transformer)

    # Register Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    return app
