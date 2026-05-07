import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ml_api.core.config import get_settings
from ml_api.main import app


@pytest.fixture(scope="session")
def client():
    """Spin the app up once for the whole session.

    TestClient runs the full ASGI lifespan: the model is loaded from disk
    and a SQL Server connection pool is opened.  Both are expensive, so we
    share a single instance across every test in this module.
    """
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
