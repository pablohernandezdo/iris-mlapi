import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import make_url, text

from ml_api.core.config import get_settings
from ml_api.db.database import SQLServerDatabaseService
from ml_api.ml.model_service import ModelService

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = settings.model_path  # use the real path from settings
    try:
        logger.info("Loading model at startup: model_path=%s", model_path)
        app.state.model_service = ModelService(model_path)
        logger.info("Model loaded successfully")
    except Exception as exc:
        logger.critical("Startup failed: model could not be loaded", exc_info=True)
        # Wrap unknown errors as domain error if needed
        raise exc

    try:
        db_url = settings.db_url.get_secret_value()
        parsed = make_url(db_url)
        logger.info(
            "Initializing database connection at startup: host=%s database=%s",
            parsed.host,
            parsed.database,
        )
        app.state.database_service = SQLServerDatabaseService(
            connection_string=db_url,
        )

        logger.info("Verifying database connection at startup")
        with app.state.database_service.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("Database connection initialized successfully")
    except Exception as exc:
        logger.critical(
            "Startup failed: database connection could not be initialized",
            exc_info=True,
        )
        raise exc

    yield
