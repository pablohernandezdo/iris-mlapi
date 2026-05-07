import logging

from fastapi import APIRouter

from ml_api.api.schemas import (
    ErrorResponse,
    InputFeatures,
    PredictionResult,
)
from ml_api.api.services.prediction_service import PredictionService
from ml_api.db.database import DbSession
from ml_api.db.repositories.prediction_repository import PredictionRepository
from ml_api.ml.model_service import ModelServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/predict",
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def predict(
    db: DbSession, features: InputFeatures, model: ModelServiceDep
) -> PredictionResult:
    service = PredictionService(model, PredictionRepository(db))
    return service.predict_and_save(features)
