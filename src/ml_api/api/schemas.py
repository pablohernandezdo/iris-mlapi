from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt


class InputFeatures(BaseModel):
    # how do I choose the right constraints based on training data?
    sepal_length: StrictFloat = Field(..., gt=0, lt=10)
    sepal_width: StrictFloat = Field(..., gt=0, lt=10)
    petal_length: StrictFloat = Field(..., gt=0, lt=10)
    petal_width: StrictFloat = Field(..., gt=0, lt=10)

    model_config = ConfigDict(extra="forbid")


class PredictionResult(BaseModel):
    idx: StrictInt
    class_name: str

    model_config = ConfigDict(extra="forbid")


class HealthStatus(BaseModel):
    status: str

    model_config = ConfigDict(extra="forbid")


class ErrorDetail(BaseModel):
    type: str
    message: str
    details: Optional[list[Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PredictionRecord(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    predicted_class: int
    created_at: datetime
