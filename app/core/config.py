"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

CSV_PATH_ENV = "MOVIES_CSV_PATH"


class ConfigurationError(RuntimeError):
    """Raised when a required setting is missing."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings of the application.

    Attributes:
        csv_path: Path of the CSV file loaded into the database on startup.
        api_prefix: URL prefix shared by every API route.
    """

    csv_path: Path
    api_prefix: str = "/api/v1"

    @classmethod
    def from_env(cls) -> "Settings":
        """Build the settings from environment variables.

        Required variables:
            ``MOVIES_CSV_PATH``: path of the movie list CSV.

        Returns:
            The resolved settings.

        Raises:
            ConfigurationError: If ``MOVIES_CSV_PATH`` is not set.
        """
        csv_path = os.getenv(CSV_PATH_ENV)
        if not csv_path:
            raise ConfigurationError(
                f"Environment variable {CSV_PATH_ENV} must point to the movie list CSV"
            )
        return cls(csv_path=Path(csv_path))
