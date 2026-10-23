"""Movie, producer and studio ORM models."""

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class Producer(Base):
    """A producer credited on one or more movies."""

    __tablename__ = "producers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_producers, back_populates="producers"
    )


class Studio(Base):
    """A studio credited on one or more movies."""

    __tablename__ = "studios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

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
