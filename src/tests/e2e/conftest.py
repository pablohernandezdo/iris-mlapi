from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ml_api.core.config import get_settings
from ml_api.main import app

# Committed fixture model — small sklearn pipeline with the same structure as prod.
# Kept under src/tests/ so it lands in the test image via `COPY src/tests/ src/tests/`.
# data/ is in .dockerignore and is never baked into any image.
_FIXTURE_MODEL_PATH = "src/tests/fixtures/iris_test_pipeline.pkl"


def _load_model_from_disk(_blob_url: str) -> bytes:
    """Test stand-in for _download_model.

    Returns bytes from the committed fixture model instead of hitting Azure
    Blob Storage.  No Azure credentials are required.
    """
    with open(_FIXTURE_MODEL_PATH, "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def client():
    """Spin the app up once for the whole session.

    The Azure blob download is patched out so no Azure credentials are needed
    in the test environment. Everything else (lifespan, DB, model inference)
    runs for real.
    """
    with patch(
        "ml_api.core.lifespan._download_model", side_effect=_load_model_from_disk
    ):
        with TestClient(app) as c:
            yield c


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(get_settings().db_url.get_secret_value())
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_predictions(db_engine):
    """Wipe the predictions table before every test.

    Because `client` is session-scoped the app (and its DB pool) stays up
    the whole time, so rows written by one test would bleed into the next
    without this cleanup step.
    """
    with Session(db_engine) as session:
        session.execute(text("DELETE FROM predictions"))
        session.commit()
    yield
