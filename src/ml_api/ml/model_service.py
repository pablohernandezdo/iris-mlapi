import logging
import os
from typing import Annotated

import joblib  # type: ignore
from fastapi import Depends, Request

from ml_api.api.schemas import InputFeatures, PredictionResult

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self, pipe_path: str):
        logger.info(f"Loading model pipeline from {pipe_path}")

        if not os.path.exists(pipe_path):
            logger.error(f"Model pipeline file not found at {pipe_path}")
            raise FileNotFoundError(f"Model pipeline file not found at {pipe_path}")

        self.pipe = joblib.load(pipe_path)  # type:ignore

        if (
            self.pipe is None
            or "model" not in self.pipe
            or "class_names" not in self.pipe
        ):
            logger.error("Invalid model pipeline structure")
            raise Exception("Invalid model pipeline structure")

        logger.info("Model pipeline loaded successfully")

        self.model = self.pipe["model"]
        self.class_names = self.pipe["class_names"]

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
