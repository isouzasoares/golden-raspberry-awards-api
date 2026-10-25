"""Integration tests for ``GET /api/v1/producers/award-intervals``."""

from fastapi.testclient import TestClient

from tests.integration.conftest import ClientFactory

URL = "/api/v1/producers/award-intervals"


def interval(producer: str, previous: int, following: int) -> dict:
    return {
        "producer": producer,
        "interval": following - previous,
        "previousWin": previous,
        "followingWin": following,
    }


def test_bundled_movie_list_matches_expected_intervals(client: TestClient) -> None:
    response = client.get(URL)

    assert response.status_code == 200
    assert response.json() == {
        "min": [interval("Joel Silver", 1990, 1991)],
        "max": [interval("Matthew Vaughn", 2002, 2015)],
    }


def test_returns_every_producer_tied_for_min_and_max(
    client_for: ClientFactory,
) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1;yes
        2001;Movie B;Studio;Producer 1;yes
        2010;Movie C;Studio;Producer 2;yes
        2011;Movie D;Studio;Producer 2;yes
        1900;Movie E;Studio;Producer 3;yes
        1999;Movie F;Studio;Producer 3;yes
        2001;Movie G;Studio;Producer 4;yes
        2100;Movie H;Studio;Producer 4;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [
        interval("Producer 1", 2000, 2001),
        interval("Producer 2", 2010, 2011),
    ]
    assert body["max"] == [
        interval("Producer 3", 1900, 1999),
        interval("Producer 4", 2001, 2100),
    ]


def test_only_consecutive_awards_are_compared(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1;yes
        2005;Movie B;Studio;Producer 1;yes
        2007;Movie C;Studio;Producer 1;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [interval("Producer 1", 2005, 2007)]
    assert body["max"] == [interval("Producer 1", 2000, 2005)]


def test_same_producer_may_appear_in_min_and_max_multiple_times(
    client_for: ClientFactory,
) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1;yes
        2001;Movie B;Studio;Producer 1;yes
        2011;Movie C;Studio;Producer 1;yes
        2012;Movie D;Studio;Producer 1;yes
        2022;Movie E;Studio;Producer 1;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [
        interval("Producer 1", 2000, 2001),
        interval("Producer 1", 2011, 2012),
    ]
    assert body["max"] == [
        interval("Producer 1", 2001, 2011),
        interval("Producer 1", 2012, 2022),
    ]


def test_single_interval_is_both_min_and_max(client_for: ClientFactory) -> None:
    client = client_for(
        """
        1990;Movie A;Studio;Producer 1;yes
        1995;Movie B;Studio;Producer 1;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == body["max"] == [interval("Producer 1", 1990, 1995)]


def test_nominations_without_award_are_ignored(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1;yes
        2001;Movie B;Studio;Producer 1;
        2002;Movie C;Studio;Producer 1;no
        2010;Movie D;Studio;Producer 1;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == body["max"] == [interval("Producer 1", 2000, 2010)]


def test_producers_are_split_from_shared_credits(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1, Producer 2 and Producer 3;yes
        2003;Movie B;Studio;Producer 2;yes
        2004;Movie C;Studio;Producer 3, and Producer 4;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [interval("Producer 2", 2000, 2003)]
    assert body["max"] == [interval("Producer 3", 2000, 2004)]


def test_awards_in_the_same_year_have_zero_interval(
    client_for: ClientFactory,
) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1;yes
        2000;Movie B;Studio;Producer 1;yes
        2008;Movie C;Studio;Producer 1;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [interval("Producer 1", 2000, 2000)]
    assert body["max"] == [interval("Producer 1", 2000, 2008)]


def test_rows_out_of_chronological_order(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2015;Movie C;Studio;Producer 1;yes
        1990;Movie A;Studio;Producer 1;yes
        2000;Movie B;Studio;Producer 1;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [interval("Producer 1", 1990, 2000)]
    assert body["max"] == [interval("Producer 1", 2000, 2015)]


def test_empty_lists_when_no_producer_won_twice(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1;yes
        2001;Movie B;Studio;Producer 2;yes
        2002;Movie C;Studio;Producer 1;
        """
    )

    response = client.get(URL)

    assert response.status_code == 200
    assert response.json() == {"min": [], "max": []}


def test_unsupported_method_is_rejected(client: TestClient) -> None:
    assert client.post(URL).status_code == 405


def test_producer_names_match_regardless_of_case_and_spacing(
    client_for: ClientFactory,
) -> None:
    client = client_for(
        """
        1990;Movie A;Studio;JOEL SILVER;yes
        1991;Movie B;Studio;Joel Silver;yes
        2000;Movie C;Studio;joel   silver;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [interval("Joel Silver", 1990, 1991)]
    assert body["max"] == [interval("Joel Silver", 1991, 2000)]


def test_separators_are_recognized_in_any_case(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Producer 1 AND Producer 2;yes
        2002;Movie B;Studio;Producer 2 & Producer 3;yes
        2005;Movie C;Studio;Producer 3, Producer 4, And Producer 1;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [interval("Producer 2", 2000, 2002)]
    assert body["max"] == [interval("Producer 1", 2000, 2005)]


def test_names_containing_and_are_not_split(client_for: ClientFactory) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;Wes Anderson and Sandra Bland;yes
        2004;Movie B;Studio;Wes Anderson;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == body["max"] == [interval("Wes Anderson", 2000, 2004)]


def test_producer_names_match_regardless_of_accents_and_punctuation(
    client_for: ClientFactory,
) -> None:
    client = client_for(
        """
        2000;Movie A;Studio;José Ferrer and Robert W. Cort;yes
        2003;Movie B;Studio;Jose Ferrer;yes
        2010;Movie C;Studio;Robert W Cort;yes
        """
    )

    body = client.get(URL).json()

    assert body["min"] == [interval("José Ferrer", 2000, 2003)]
    assert body["max"] == [interval("Robert W. Cort", 2000, 2010)]
