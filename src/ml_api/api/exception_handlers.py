import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ml_api.api.schemas import ErrorDetail, ErrorResponse
from ml_api.db.exceptions import DatabaseSaveError
from ml_api.ml.exceptions import PredictionError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error", extra={"errors": exc.errors()})

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                type="validation_error",
                message="Invalid input",
                details=list(exc.errors()),
            )
        ).model_dump(),
    )


async def prediction_exception_handler(request: Request, exc: PredictionError):
    logger.error(
        f"Prediction error - Features: {exc.features}",
        extra={"features": exc.features},
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(type="prediction_error", message=str(exc), details=None)
        ).model_dump(),
    )


async def database_save_exception_handler(request: Request, exc: DatabaseSaveError):
    logger.error("Failed to save prediction to database", exc_info=exc)

    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error=ErrorDetail(
                type="database_error",
                message="Failed to save prediction to database",
                details=None,
            )
        ).model_dump(),
    )
