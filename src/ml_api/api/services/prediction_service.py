from ml_api.api.schemas import InputFeatures, PredictionResult
from ml_api.db.repositories.prediction_repository import PredictionRepository
from ml_api.ml.model_service import ModelService


class PredictionService:
    def __init__(self, model: ModelService, repo: PredictionRepository):
        self.model = model
        self.repo = repo

    def predict_and_save(self, features: InputFeatures) -> PredictionResult:
        result = self.model.predict(features)
        self.repo.save(features, result.idx)  # raises DatabaseSaveError on failure
        return result
