from io import BytesIO
from unittest.mock import patch

import joblib
import pytest

from ml_api.api.schemas import InputFeatures
from ml_api.ml.exceptions import ModelLoadError
from ml_api.ml.model_service import ModelService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FixedPredictor:
    """Minimal picklable model stub with a configurable predict return value."""

    def __init__(self, return_index: int = 0):
        self.return_index = return_index
        self.last_call_args = None

    def predict(self, X):
        self.last_call_args = X
        return [self.return_index]


_CLASS_NAMES = ["setosa", "versicolor", "virginica"]


def _make_artifact_bytes(model=None, class_names=_CLASS_NAMES) -> bytes:
    artifact = {"model": model or _FixedPredictor(), "class_names": class_names}
    buf = BytesIO()
    joblib.dump(artifact, buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# __init__ — deserialization errors
# ---------------------------------------------------------------------------


def test_init_raises_on_corrupt_bytes():
    with pytest.raises(ModelLoadError, match="Failed to deserialize"):
        ModelService(b"not a valid pickle")


def test_init_raises_when_joblib_load_returns_none():
    with patch("ml_api.ml.model_service.joblib.load", return_value=None):
        with pytest.raises(ModelLoadError, match="Invalid model pipeline structure"):
            ModelService(b"irrelevant")


# ---------------------------------------------------------------------------
# __init__ — structural validation
# ---------------------------------------------------------------------------


def test_init_raises_when_model_key_missing():
    buf = BytesIO()
    joblib.dump({"class_names": ["setosa"]}, buf)
    with pytest.raises(ModelLoadError, match="Invalid model pipeline structure"):
        ModelService(buf.getvalue())


def test_init_raises_when_class_names_key_missing():
    buf = BytesIO()
    joblib.dump({"model": _FixedPredictor()}, buf)
    with pytest.raises(ModelLoadError, match="Invalid model pipeline structure"):
        ModelService(buf.getvalue())


def test_init_sets_model_and_class_names_from_artifact():
    svc = ModelService(_make_artifact_bytes())

    assert svc.class_names == _CLASS_NAMES


# ---------------------------------------------------------------------------
# predict()
# ---------------------------------------------------------------------------


def test_predict_passes_features_to_model_in_correct_order():
    svc = ModelService(_make_artifact_bytes(model=_FixedPredictor(return_index=0)))

    features = InputFeatures(
        sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
    )
    svc.predict(features)

    assert svc.model.last_call_args == [[5.1, 3.5, 1.4, 0.2]]


@pytest.mark.parametrize("idx,name", enumerate(_CLASS_NAMES))
def test_predict_returns_correct_class_name_for_index(idx, name):
    svc = ModelService(_make_artifact_bytes(model=_FixedPredictor(return_index=idx)))

    features = InputFeatures(
        sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
    )
    result = svc.predict(features)

    assert result.idx == idx
    assert result.class_name == name
