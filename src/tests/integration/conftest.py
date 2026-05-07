import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from ml_api.core.config import get_settings


@pytest.fixture
def db_session():
    engine = create_engine(get_settings().db_url.get_secret_value())
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_predictions(db_session: Session):
    """Truncate the predictions table before every integration test.

    This guards against leftover rows from failed previous runs while
    keeping each test isolated from the next.  Tests themselves do not
    commit (only the repo save path does), so no explicit post-test
    cleanup is required.
    """
    db_session.execute(text("DELETE FROM predictions"))
    db_session.commit()
    yield
