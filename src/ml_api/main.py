import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from ml_api.api.exception_handlers import (
    database_save_exception_handler,
    prediction_exception_handler,
    validation_exception_handler,
)
from ml_api.api.routes.health import router as health_router
from ml_api.api.routes.predict import router as predict_router
from ml_api.api.routes.query import router as query_router
from ml_api.core.config import get_settings
from ml_api.core.lifespan import lifespan
from ml_api.core.logger import setup_logger
from ml_api.db.exceptions import DatabaseSaveError
from ml_api.ml.exceptions import PredictionError

setup_logger(level=get_settings().log_level, env=get_settings().env)
logger = logging.getLogger(__name__)

settings = get_settings()
logger.info(
    "Settings loaded: env=%s app_name=%s model_blob_url=%s",
    settings.env,
    settings.app_name,
    settings.model_blob_url,
)

app = FastAPI(lifespan=lifespan)
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
app.add_exception_handler(PredictionError, prediction_exception_handler)  # type: ignore
app.add_exception_handler(DatabaseSaveError, database_save_exception_handler)  # type: ignore

app.include_router(predict_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
app.include_router(health_router)
