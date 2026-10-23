"""Producer endpoints."""

from fastapi import APIRouter

from app.controllers.dependencies import SessionDep
from app.repositories.producer_repository import ProducerRepository
from app.schemas.producer import ProducerAwardIntervals
from app.services.award_intervals import AwardIntervalService

router = APIRouter(prefix="/producers", tags=["producers"])


@router.get(
    "/award-intervals",
    response_model=ProducerAwardIntervals,
    summary="Shortest and longest intervals between awards",
)
def get_award_intervals(session: SessionDep) -> ProducerAwardIntervals:
    """Return the producers with the shortest and longest gap between two wins."""
    return AwardIntervalService(ProducerRepository(session)).get_extreme_intervals()
