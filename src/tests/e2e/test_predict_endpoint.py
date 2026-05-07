from fastapi.testclient import TestClient

VALID_FEATURES = {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2,
}


def test_predict_returns_prediction_result(client: TestClient):
    """A well-formed request gets a 200 with idx (int) and class_name (str)."""
    response = client.post("/api/v1/predict", json=VALID_FEATURES)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["idx"], int)
    assert isinstance(body["class_name"], str) and body["class_name"]


def test_predict_persists_to_database(client: TestClient):
    """After a successful prediction the record must appear in /get_all_predictions."""
    client.post("/api/v1/predict", json=VALID_FEATURES)

    query_response = client.get("/api/v1/get_all_predictions")
    assert query_response.status_code == 200
    records = query_response.json()
    assert len(records) == 1
    assert records[0]["sepal_length"] == VALID_FEATURES["sepal_length"]
    assert records[0]["predicted_class"] == 0  # known output for these features


def test_predict_rejects_missing_field(client: TestClient):
    """Omitting a required field must return 422 with type=validation_error."""
    payload = {k: v for k, v in VALID_FEATURES.items() if k != "petal_width"}
    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"


def test_predict_rejects_extra_field(client: TestClient):
    """Extra fields are forbidden by the schema (extra='forbid')."""
    payload = {**VALID_FEATURES, "unexpected_field": 1.0}
    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"


def test_predict_rejects_out_of_range_value(client: TestClient):
    """Values outside the declared bounds (gt=0, lt=10) must be rejected."""
    payload = {**VALID_FEATURES, "sepal_length": 0.0}  # violates gt=0
    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"


def test_predict_rejects_wrong_type(client: TestClient):
    """StrictFloat fields must refuse string values (no coercion)."""
    payload = {**VALID_FEATURES, "sepal_length": "not-a-number"}
    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"
