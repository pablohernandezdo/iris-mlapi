from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from ml_api.api.schemas import InputFeatures, PredictionResult
from ml_api.api.services.prediction_service import PredictionService
from ml_api.api.services.query_service import PredictionQueryService
from ml_api.db.repositories.prediction_repository import PredictionRepository

FEATURES = InputFeatures(
    sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
)


def test_predict_and_save_persists_to_database(db_session: Session):
    mock_model = MagicMock()
    mock_model.predict.return_value = PredictionResult(idx=0, class_name="setosa")
    repo = PredictionRepository(db_session)
    service = PredictionService(model=mock_model, repo=repo)

    service.predict_and_save(FEATURES)

    records = repo.get_all()
    assert len(records) == 1
    assert records[0].predicted_class == 0
    assert records[0].sepal_length == FEATURES.sepal_length


def test_query_service_get_all_returns_saved_predictions(db_session: Session):
    # Seed the DB via the repository directly
    repo = PredictionRepository(db_session)
    repo.save(FEATURES, predicted_class=1)
    repo.save(FEATURES, predicted_class=2)

    service = PredictionQueryService(repo=repo)
    records = service.get_all()

    assert len(records) == 2
    assert {r.predicted_class for r in records} == {1, 2}
