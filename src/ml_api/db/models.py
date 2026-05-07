from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer

from ml_api.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer(), primary_key=True, index=True)
    sepal_length = Column(Float(), nullable=False)
    sepal_width = Column(Float(), nullable=False)
    petal_length = Column(Float(), nullable=False)
    petal_width = Column(Float(), nullable=False)
    predicted_class = Column(Integer(), nullable=False)

    created_at = Column(
        DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
