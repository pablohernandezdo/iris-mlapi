from fastapi.testclient import TestClient

VALID_FEATURES = {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2,
}


def test_get_all_predictions_empty(client: TestClient):
    """With no prior predictions the endpoint must return an empty list."""
    response = client.get("/api/v1/get_all_predictions")

    assert response.status_code == 200
    assert response.json() == []


def test_get_all_predictions_returns_saved_records(client: TestClient):
    """Records written by /predict must be retrievable and well-formed."""
    client.post("/api/v1/predict", json=VALID_FEATURES)
    client.post("/api/v1/predict", json={**VALID_FEATURES, "sepal_length": 6.3})

    response = client.get("/api/v1/get_all_predictions")

    assert response.status_code == 200
    records = response.json()
    assert len(records) == 2

    # Every record must have the expected fields and sensible types
    for record in records:
        assert isinstance(record["sepal_length"], float)
        assert isinstance(record["predicted_class"], int)
        assert record["created_at"] is not None
