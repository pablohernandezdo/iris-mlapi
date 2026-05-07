from ml_api.api.schemas import PredictionRecord
from ml_api.db.repositories.prediction_repository import PredictionRepository


class PredictionQueryService:
    def __init__(self, repo: PredictionRepository):
        self.repo = repo

    def get_all(self) -> list[PredictionRecord]:
        return self.repo.get_all()
