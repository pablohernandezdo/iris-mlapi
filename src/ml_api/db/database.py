import logging
from typing import Annotated, Generator

from fastapi import Depends, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

logger = logging.getLogger("database")


class SQLServerDatabaseService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = create_engine(self.connection_string)


def get_db(request: Request) -> Generator[Session, None, None]:
    engine = request.app.state.database_service.engine
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


DbSession = Annotated[Session, Depends(get_db)]
