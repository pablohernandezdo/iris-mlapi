import logging

from fastapi import APIRouter

from ml_api.api.schemas import HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health():
    logger.info("Received health check request")
    return HealthStatus(status="ok")


@router.get("/health/ready")
def health_ready():
    logger.info("Received readiness check request")
    return HealthStatus(status="ok")
