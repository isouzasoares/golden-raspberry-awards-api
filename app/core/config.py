"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "movielist.csv"


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings of the application.

    Attributes:
        csv_path: Path of the CSV file loaded into the database on startup.
        api_prefix: URL prefix shared by every API route.
    """

    csv_path: Path = DEFAULT_CSV_PATH
    api_prefix: str = "/api/v1"

    @classmethod
    def from_env(cls) -> "Settings":
        """Build the settings, allowing overrides through environment variables.

        Supported variables:
            ``MOVIES_CSV_PATH``: overrides :attr:`csv_path`.

        Returns:
            The resolved settings.
        """
        csv_path = os.getenv("MOVIES_CSV_PATH")
        return cls(csv_path=Path(csv_path) if csv_path else DEFAULT_CSV_PATH)
