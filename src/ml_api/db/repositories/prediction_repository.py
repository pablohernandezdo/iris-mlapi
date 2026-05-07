from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from ml_api.api.schemas import InputFeatures, PredictionRecord
from ml_api.db.exceptions import DatabaseSaveError


class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[PredictionRecord]:
        result = self.db.execute(text("SELECT * FROM predictions")).mappings().all()
        return [PredictionRecord(**dict(row)) for row in result]

    def save(
        self,
        features: InputFeatures,
        predicted_class: int,
    ) -> None:

        try:
            self.db.execute(
                text(
                    "INSERT INTO predictions (sepal_length, sepal_width, petal_length, petal_width, predicted_class, created_at) "
                    "VALUES (:sepal_length, :sepal_width, :petal_length, :petal_width, :predicted_class, :created_at)"
                ),
                {
                    "sepal_length": features.sepal_length,
                    "sepal_width": features.sepal_width,
                    "petal_length": features.petal_length,
                    "petal_width": features.petal_width,
                    "predicted_class": predicted_class,
                    "created_at": datetime.now(timezone.utc),
                },
            )
        except Exception:
            raise DatabaseSaveError("Failed to save prediction to database")
