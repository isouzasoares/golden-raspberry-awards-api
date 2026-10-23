"""Fixtures that start the application against a given movie list."""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import DEFAULT_CSV_PATH, Settings
from app.main import create_app

CSV_HEADER = "year;title;studios;producers;winner"

ClientFactory = Callable[[str], TestClient]


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """Application loaded with the bundled movie list."""
    with TestClient(create_app(Settings(csv_path=DEFAULT_CSV_PATH))) as test_client:
        yield test_client


@pytest.fixture
def client_for(tmp_path: Path) -> Iterator[ClientFactory]:
    """Start the application with a custom movie list.

    The returned callable receives the CSV data rows (without the header)
    and returns a client whose application was loaded with them.
    """
    clients: list[TestClient] = []

    def factory(rows: str) -> TestClient:
        csv_path = tmp_path / f"movies_{len(clients)}.csv"
        csv_path.write_text(f"{CSV_HEADER}\n{rows.strip()}\n", encoding="utf-8")
        test_client = TestClient(create_app(Settings(csv_path=csv_path)))
        clients.append(test_client)
        return test_client.__enter__()

    yield factory

    for test_client in clients:
        test_client.__exit__(None, None, None)
