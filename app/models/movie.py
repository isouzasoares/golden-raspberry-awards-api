"""Movie, producer and studio ORM models."""

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.names import slugify
from app.models.base import Base

movie_producers = Table(
    "movie_producers",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("producer_id", ForeignKey("producers.id"), primary_key=True, index=True),
)

movie_studios = Table(
    "movie_studios",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("studio_id", ForeignKey("studios.id"), primary_key=True, index=True),
)


class NamedEntity:
    """Columns shared by entities identified by a human-written name.

    ``slug`` is derived from ``name`` and is the unique key, so the same name
    written with a different case, spacing, accents or punctuation maps to a
    single row.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)

    @validates("name")
    def _sync_slug(self, _key: str, value: str) -> str:
        self.slug = slugify(value)
        return value


class Producer(NamedEntity, Base):
    """A producer credited on one or more movies."""

    __tablename__ = "producers"

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_producers, back_populates="producers"
    )


class Studio(NamedEntity, Base):
    """A studio credited on one or more movies."""

    __tablename__ = "studios"

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_studios, back_populates="studios"
    )


class Movie(Base):
    """A Worst Picture nominee, flagged as winner when it took the award."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(255))
    winner: Mapped[bool] = mapped_column(default=False, index=True)

    producers: Mapped[list[Producer]] = relationship(
        secondary=movie_producers,
        back_populates="movies",
        lazy="selectin",
        order_by=Producer.name,
    )
    studios: Mapped[list[Studio]] = relationship(
        secondary=movie_studios,
        back_populates="movies",
        lazy="selectin",
        order_by=Studio.name,
    )
