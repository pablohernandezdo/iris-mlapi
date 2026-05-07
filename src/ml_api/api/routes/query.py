import logging

from fastapi import APIRouter

from ml_api.api.schemas import (
    ErrorResponse,
    PredictionRecord,
)
from ml_api.api.services.query_service import PredictionQueryService
from ml_api.db.database import DbSession
from ml_api.db.repositories.prediction_repository import PredictionRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/get_all_predictions",
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def get_all_predictions(db: DbSession) -> list[PredictionRecord]:
    service = PredictionQueryService(PredictionRepository(db))
    return service.get_all()
