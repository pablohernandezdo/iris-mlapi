import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from ml_api.api.schemas import InputFeatures
from ml_api.db.exceptions import DatabaseSaveError
from ml_api.db.repositories.prediction_repository import PredictionRepository

FEATURES = InputFeatures(
    sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
)


def test_get_all_returns_empty_list_when_no_records(db_session: Session):
    repo = PredictionRepository(db_session)

    result = repo.get_all()

    assert result == []


def test_save_persists_prediction(db_session):
    repo = PredictionRepository(db_session)

    repo.save(FEATURES, predicted_class=0)

    records = repo.get_all()
    assert len(records) == 1
    assert records[0].sepal_length == FEATURES.sepal_length
    assert records[0].sepal_width == FEATURES.sepal_width
    assert records[0].petal_length == FEATURES.petal_length
    assert records[0].petal_width == FEATURES.petal_width
    assert records[0].predicted_class == 0


def test_get_all_returns_all_saved_predictions(db_session):
    repo = PredictionRepository(db_session)
    repo.save(FEATURES, predicted_class=0)
    repo.save(FEATURES, predicted_class=1)

    records = repo.get_all()

    assert len(records) == 2
    assert {r.predicted_class for r in records} == {0, 1}


def test_save_raises_database_save_error_on_db_failure(db_session: Session):
    db_session.execute(text("EXEC sp_rename 'predictions', 'predictions_temp'"))
    db_session.commit()
    try:
        repo = PredictionRepository(db_session)
        with pytest.raises(DatabaseSaveError):
            repo.save(FEATURES, predicted_class=0)
    finally:
        db_session.execute(text("EXEC sp_rename 'predictions_temp', 'predictions'"))
        db_session.commit()
