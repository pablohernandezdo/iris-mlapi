import logging
from io import BytesIO
from typing import Annotated

import joblib  # type: ignore
from fastapi import Depends, Request

from ml_api.api.schemas import InputFeatures, PredictionResult
from ml_api.ml.exceptions import ModelLoadError

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self, model_bytes: bytes):
        try:
            self.pipe = joblib.load(BytesIO(model_bytes))
        except Exception as exc:
            raise ModelLoadError("Failed to deserialize model pipeline") from exc

        if (
            self.pipe is None
            or "model" not in self.pipe
            or "class_names" not in self.pipe
        ):
            raise ModelLoadError(
                "Invalid model pipeline structure: missing 'model' or 'class_names' keys"
            )

        self.model = self.pipe["model"]
        self.class_names = self.pipe["class_names"]
        logger.info("Model pipeline loaded successfully")

    def predict(self, features: InputFeatures) -> PredictionResult:
        input_data = [
            [
                features.sepal_length,
                features.sepal_width,
                features.petal_length,
                features.petal_width,
            ]
        ]

        logger.debug(f"Input data for prediction: {input_data}")
        pred_class_index = int(self.model.predict(input_data)[0])
        pred_class_name = self.class_names[pred_class_index]

        logger.debug(
            f"Returning prediction result: {pred_class_index}, {pred_class_name}"
        )

        return PredictionResult(idx=pred_class_index, class_name=pred_class_name)


def get_model_service(request: Request) -> ModelService:
    return request.app.state.model_service


ModelServiceDep = Annotated[ModelService, Depends(get_model_service)]
