"""Integration tests for the ``/api/v1/movies`` resource."""

import csv

import pytest
from fastapi.testclient import TestClient

from app.core.config import CSV_PATH_ENV, ConfigurationError, Settings
from app.main import create_app
from app.services.movie_importer import MovieImportError
from tests.integration.conftest import BUNDLED_CSV_PATH, ClientFactory

URL = "/api/v1/movies"


def load_bundled_rows() -> list[dict[str, str]]:
    with BUNDLED_CSV_PATH.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file, delimiter=";"))


def test_every_csv_row_is_imported(client: TestClient) -> None:
    rows = load_bundled_rows()

    body = client.get(URL, params={"limit": 500}).json()

    assert body["total"] == len(rows) == 206
    assert [(m["year"], m["title"]) for m in body["items"]] == sorted(
        (int(row["year"]), row["title"]) for row in rows
    )


def test_winners_match_csv(client: TestClient) -> None:
    expected = {
        (int(row["year"]), row["title"])
        for row in load_bundled_rows()
        if row["winner"] == "yes"
    }

    body = client.get(URL, params={"winner": True, "limit": 500}).json()

    assert body["total"] == len(expected) == 42
    assert {(m["year"], m["title"]) for m in body["items"]} == expected


def test_filter_by_year(client: TestClient) -> None:
    body = client.get(URL, params={"year": 1980}).json()

    assert body["total"] == 10
    assert {movie["year"] for movie in body["items"]} == {1980}


def test_pagination(client: TestClient) -> None:
    first = client.get(URL, params={"limit": 5, "offset": 0}).json()
    second = client.get(URL, params={"limit": 5, "offset": 5}).json()

    assert first["limit"] == second["limit"] == 5
    assert len(first["items"]) == len(second["items"]) == 5
    assert {m["id"] for m in first["items"]}.isdisjoint(
        m["id"] for m in second["items"]
    )


def test_get_movie_by_id(client: TestClient) -> None:
    response = client.get(f"{URL}/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "year": 1980,
        "title": "Can't Stop the Music",
        "studios": ["Associated Film Distribution"],
        "producers": ["Allan Carr"],
        "winner": True,
    }


def test_studios_and_producers_are_split(client: TestClient) -> None:
    body = client.get(URL, params={"year": 1984, "winner": True}).json()

    assert body["items"][0]["title"] == "Bolero"
    assert body["items"][0]["producers"] == ["Bo Derek"]

    movie = next(
        m
        for m in client.get(URL, params={"year": 1986, "limit": 50}).json()["items"]
        if m["title"] == "Under the Cherry Moon"
    )
    assert movie["producers"] == ["Bob Cavallo", "Joe Ruffalo", "Steve Fargnoli"]


def test_unknown_movie_returns_404(client: TestClient) -> None:
    response = client.get(f"{URL}/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Movie 9999 not found"}


@pytest.mark.parametrize(
    "path",
    [f"{URL}/abc", f"{URL}/0", f"{URL}?limit=0", f"{URL}?offset=-1"],
)
def test_invalid_parameters_return_422(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 422


def test_resource_is_read_only(client: TestClient) -> None:
    assert client.post(URL, json={}).status_code == 405
    assert client.delete(f"{URL}/1").status_code == 405


def test_custom_movie_list_is_loaded(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2020;First;Studio A, Studio B;Producer 1;yes
        2021;Second;Studio A;Producer 2 and Producer 3;
        """
    )

    body = client.get(URL).json()

    assert body["total"] == 2
    assert body["items"][0]["studios"] == ["Studio A", "Studio B"]
    assert body["items"][1]["producers"] == ["Producer 2", "Producer 3"]
    assert body["items"][1]["winner"] is False


def test_names_are_split_and_deduplicated(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2020;First;Studio A AND studio a & Studio B;JOEL SILVER, Joel Silver;yes
        2021;Second;STUDIO B;joel silver and Steven Perry;
        """
    )

    first, second = client.get(URL).json()["items"]

    assert first["studios"] == ["Studio A", "Studio B"]
    assert first["producers"] == ["Joel Silver"]
    assert second["studios"] == ["Studio B"]
    assert second["producers"] == ["Joel Silver", "Steven Perry"]


def test_commas_without_spaces_separate_names(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2020;First;Fox,MGM ,Lionsgate;Joel Silver,Steven Perry,AND Jon Peters;yes
        """
    )

    (movie,) = client.get(URL).json()["items"]

    assert movie["studios"] == ["Fox", "Lionsgate", "MGM"]
    assert movie["producers"] == ["Joel Silver", "Jon Peters", "Steven Perry"]


def test_startup_fails_on_invalid_csv(tmp_path) -> None:
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(
        "year;title;studios;producers;winner\nnineteen;Movie;Studio;Producer;yes\n",
        encoding="utf-8",
    )

    with (
        pytest.raises(MovieImportError, match="Line 2: invalid year"),
        TestClient(create_app(Settings(csv_path=csv_path))),
    ):
        pass


def test_csv_path_is_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(CSV_PATH_ENV, str(BUNDLED_CSV_PATH))

    with TestClient(create_app()) as client:
        assert client.get(URL).json()["total"] == 206


def test_startup_requires_csv_path(monkeypatch) -> None:
    monkeypatch.delenv(CSV_PATH_ENV, raising=False)

    with pytest.raises(ConfigurationError, match=CSV_PATH_ENV):
        create_app()
