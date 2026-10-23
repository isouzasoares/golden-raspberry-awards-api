"""Movie payloads."""

from pydantic import Field, field_validator

from app.schemas.base import ApiSchema


class MovieRead(ApiSchema):
    """A Worst Picture nominee."""

    id: int
    year: int
    title: str
    studios: list[str]
    producers: list[str]
    winner: bool

    @field_validator("studios", "producers", mode="before")
    @classmethod
    def _names(cls, value: list) -> list[str]:
        """Accept ORM entities as well as plain names."""
        return [getattr(item, "name", item) for item in value]


class MoviePage(ApiSchema):
    """A page of movies."""

    items: list[MovieRead]
    total: int = Field(description="Number of movies matching the filters.")
    limit: int
    offset: int
