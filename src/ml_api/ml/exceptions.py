from typing import Optional

from ml_api.api.schemas import InputFeatures


class PredictionError(Exception):
    def __init__(self, msg: str, *, features: Optional[InputFeatures] = None) -> None:
        super().__init__(msg)
        self.msg = msg
        self.features = features


class ModelLoadError(Exception):
    """Raised when the model cannot be downloaded or instantiated at startup."""

    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg
