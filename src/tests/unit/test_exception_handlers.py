import json
from unittest.mock import MagicMock

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from ml_api.api.exception_handlers import (
    database_save_exception_handler,
    prediction_exception_handler,
    validation_exception_handler,
)
from ml_api.db.exceptions import DatabaseSaveError
from ml_api.ml.exceptions import PredictionError


async def test_validation_exception_handler_returns_422_with_error_details():
    mock_request = MagicMock(spec=Request)
    errors = [  # type:ignore
        {
            "type": "missing",
            "loc": ["body", "sepal_length"],
            "msg": "Field required",
            "input": {},
        }
    ]
    mock_exc = MagicMock(spec=RequestValidationError)
    mock_exc.errors.return_value = errors

    response = await validation_exception_handler(mock_request, mock_exc)

    assert response.status_code == 422
    body = json.loads(response.body)
    assert body["error"]["type"] == "validation_error"
    assert body["error"]["message"] == "Invalid input"
    assert body["error"]["details"] == errors


async def test_prediction_exception_handler_returns_500_with_exception_message():
    mock_request = MagicMock(spec=Request)
    exc = PredictionError("model exploded")

    response = await prediction_exception_handler(mock_request, exc)

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["error"]["type"] == "prediction_error"
    assert body["error"]["message"] == "model exploded"
    assert body["error"]["details"] is None


async def test_database_save_exception_handler_returns_503():
    mock_request = MagicMock(spec=Request)
    exc = DatabaseSaveError("db write failed")

    response = await database_save_exception_handler(mock_request, exc)

    assert response.status_code == 503
    body = json.loads(response.body)
    assert body["error"]["type"] == "database_error"
    assert body["error"]["message"] == "Failed to save prediction to database"
    assert body["error"]["details"] is None
