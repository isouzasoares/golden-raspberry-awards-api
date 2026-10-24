"""Producer endpoints."""

from fastapi import APIRouter

from app.controllers.dependencies import AwardIntervalServiceDep
from app.schemas.producer import ProducerAwardIntervals

router = APIRouter(prefix="/producers", tags=["producers"])


@router.get(
    "/award-intervals",
    response_model=ProducerAwardIntervals,
    summary="Shortest and longest intervals between awards",
)
def get_award_intervals(service: AwardIntervalServiceDep) -> ProducerAwardIntervals:
    """Return the producers with the shortest and longest gap between two wins."""
    return service.get_extreme_intervals()
