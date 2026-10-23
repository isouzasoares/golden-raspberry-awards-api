"""Import of the movie list CSV into the database."""

import csv
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Movie, Producer, Studio

CSV_DELIMITER = ";"
REQUIRED_COLUMNS = frozenset({"year", "title", "studios", "producers", "winner"})
WINNER_FLAG = "yes"

# Splits "A, B and C" (also "A, B, and C") into ["A", "B", "C"].
_NAME_SEPARATOR = re.compile(r"\s*,\s*(?:and\s+)?|\s+and\s+")


class MovieImportError(ValueError):
    """Raised when the CSV file cannot be imported."""


@dataclass(frozen=True, slots=True)
class MovieRecord:
    """A validated row of the movie list CSV."""

    year: int
    title: str
    studios: tuple[str, ...]
    producers: tuple[str, ...]
    winner: bool


def split_names(raw: str) -> tuple[str, ...]:
    """Split a list of names written in natural language.

    Duplicates are removed while preserving the original order.

    Args:
        raw: Names separated by commas and/or ``and``, e.g. ``"A, B and C"``.

    Returns:
        The individual names.

    Examples:
        >>> split_names("Allan Carr, Bob Cavallo and Joe Ruffalo")
        ('Allan Carr', 'Bob Cavallo', 'Joe Ruffalo')
    """
    names = (name.strip() for name in _NAME_SEPARATOR.split(raw))
    return tuple(dict.fromkeys(name for name in names if name))


def read_movie_records(csv_path: Path) -> Iterator[MovieRecord]:
    """Parse and validate the rows of the movie list CSV.

    Args:
        csv_path: Path of a ``;``-delimited CSV file with the columns
            ``year;title;studios;producers;winner``.

    Yields:
        One record per non-empty data row.

    Raises:
        MovieImportError: If the file is missing, a required column is
            absent or a row holds invalid data.
    """
    try:
        csv_file = csv_path.open(encoding="utf-8-sig", newline="")
    except OSError as error:
        raise MovieImportError(
            f"Cannot open movie list '{csv_path}': {error}"
        ) from error

    with csv_file:
        reader = csv.DictReader(csv_file, delimiter=CSV_DELIMITER)
        header = {(column or "").strip().lower() for column in reader.fieldnames or ()}
        if missing := REQUIRED_COLUMNS - header:
            raise MovieImportError(
                f"Movie list '{csv_path}' is missing columns: {sorted(missing)}"
            )

        for row in reader:
            normalized = {
                (key or "").strip().lower(): (value or "").strip()
                for key, value in row.items()
            }
            if not any(normalized.values()):
                continue
            yield _parse_row(normalized, line=reader.line_num)


def _parse_row(row: dict[str, str], line: int) -> MovieRecord:
    """Convert a normalized CSV row into a :class:`MovieRecord`.

    Args:
        row: Row with lower-cased keys and stripped values.
        line: Line number of the row, used in error messages.

    Returns:
        The parsed record.

    Raises:
        MovieImportError: If the year is not an integer or the title is empty.
    """
    try:
        year = int(row["year"])
    except ValueError as error:
        raise MovieImportError(f"Line {line}: invalid year {row['year']!r}") from error

    if not row["title"]:
        raise MovieImportError(f"Line {line}: title is required")

    return MovieRecord(
        year=year,
        title=row["title"],
        studios=split_names(row["studios"]),
        producers=split_names(row["producers"]),
        winner=row["winner"].lower() == WINNER_FLAG,
    )


class MovieImporter:
    """Persist movie records, reusing producers and studios by name."""

    def __init__(self, session: Session) -> None:
        """Initialize the importer.

        Args:
            session: Session used to persist the records.
        """
        self._session = session
        self._producers = {p.name: p for p in session.scalars(select(Producer))}
        self._studios = {s.name: s for s in session.scalars(select(Studio))}

    def import_csv(self, csv_path: Path) -> int:
        """Load every movie of a CSV file in a single transaction.

        Args:
            csv_path: Path of the movie list CSV.

        Returns:
            The number of imported movies.

        Raises:
            MovieImportError: If the file is invalid; nothing is persisted.
        """
        return self.import_records(read_movie_records(csv_path))

    def import_records(self, records: Iterable[MovieRecord]) -> int:
        """Persist the given records in a single transaction.

        Args:
            records: Records to persist.

        Returns:
            The number of imported movies.
        """
        imported = 0
        for record in records:
            # Adding each movie as soon as it is built keeps the generated ids
            # in file order (cascades would otherwise reorder the inserts).
            self._session.add(self._build_movie(record))
            imported += 1
        self._session.commit()
        return imported

    def _build_movie(self, record: MovieRecord) -> Movie:
        return Movie(
            year=record.year,
            title=record.title,
            winner=record.winner,
            producers=[self._get_or_create_producer(n) for n in record.producers],
            studios=[self._get_or_create_studio(n) for n in record.studios],
        )

    def _get_or_create_producer(self, name: str) -> Producer:
        if name not in self._producers:
            self._producers[name] = Producer(name=name)
        return self._producers[name]

    def _get_or_create_studio(self, name: str) -> Studio:
        if name not in self._studios:
            self._studios[name] = Studio(name=name)
        return self._studios[name]
