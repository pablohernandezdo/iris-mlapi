import logging
from contextlib import asynccontextmanager

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient
from fastapi import FastAPI
from sqlalchemy import make_url, text

from ml_api.core.config import get_settings
from ml_api.db.database import SQLServerDatabaseService
from ml_api.ml.exceptions import ModelLoadError
from ml_api.ml.model_service import ModelService

logger = logging.getLogger(__name__)
settings = get_settings()


def _download_model(blob_url: str) -> bytes:
    """Download the model blob using DefaultAzureCredential.

    Locally: resolves to the AzureCliCredential (az login).
    In production: resolves to the ManagedIdentityCredential.
    """
    logger.info("Downloading model from blob: %s", blob_url)
    credential = DefaultAzureCredential()
    blob_client = BlobClient.from_blob_url(blob_url, credential=credential)
    try:
        model_bytes: bytes = blob_client.download_blob().readall()
    except Exception as exc:
        raise ModelLoadError(f"Failed to download model blob: {exc}") from exc
    logger.info("Model blob downloaded successfully (%d bytes)", len(model_bytes))
    return model_bytes


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        model_bytes = _download_model(settings.model_blob_url)
        app.state.model_service = ModelService(model_bytes)
    except ModelLoadError:
        logger.critical("Startup failed: model could not be loaded", exc_info=True)
        raise

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
