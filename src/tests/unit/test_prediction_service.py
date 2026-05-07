from unittest.mock import MagicMock

import pytest

from ml_api.api.schemas import InputFeatures, PredictionResult
from ml_api.api.services.prediction_service import PredictionService
from ml_api.db.exceptions import DatabaseSaveError


def test_predict_and_save_calls_model_with_features():
    mock_model = MagicMock()
    mock_repo = MagicMock()

    service = PredictionService(model=mock_model, repo=mock_repo)
    features = InputFeatures(
        sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
    )
    _ = service.predict_and_save(features)

    mock_model.predict.assert_called_once_with(features)


def test_predict_and_save_calls_repo_with_correct_args():
    mock_model = MagicMock()
    mock_repo = MagicMock()

    expected_result = PredictionResult(idx=0, class_name="setosa")
    mock_model.predict.return_value = expected_result

    service = PredictionService(model=mock_model, repo=mock_repo)
    features = InputFeatures(
        sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
    )
    _ = service.predict_and_save(features)

    mock_repo.save.assert_called_once_with(features, expected_result.idx)


def test_predict_and_save_returns_model_result():
    mock_model = MagicMock()
    mock_repo = MagicMock()
    expected_result = PredictionResult(idx=0, class_name="setosa")
    mock_model.predict.return_value = expected_result

    service = PredictionService(model=mock_model, repo=mock_repo)
    features = InputFeatures(
        sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
    )
    result = service.predict_and_save(features)

    assert result == expected_result


def test_predict_and_save_propagates_database_save_error():
    mock_model = MagicMock()
    mock_repo = MagicMock()
    mock_repo.save.side_effect = DatabaseSaveError("Failed to save")

    service = PredictionService(model=mock_model, repo=mock_repo)
    features = InputFeatures(
        sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
    )

    with pytest.raises(DatabaseSaveError):
        service.predict_and_save(features)
