# Golden Raspberry Awards API

RESTful API that exposes the nominees and winners of the Golden Raspberry Awards
*Worst Picture* category, including the producers with the shortest and the
longest interval between two consecutive awards.

The movie list CSV is loaded into an in-memory SQLite database every time the
application starts, so no database installation is required.

## Tech stack

- Python 3.11+
- [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn
- SQLAlchemy 2.0 on top of an embedded, in-memory SQLite database
- Docker / Docker Compose (optional)
- pytest for the integration tests, ruff for linting (PEP 8 / PEP 257)

## Movie list

The application does not ship with a hard-coded dataset: the CSV to load is
always given through the `MOVIES_CSV_PATH` environment variable. The file must
be `;`-delimited with the header `year;title;studios;producers;winner`, where
`winner` is `yes` for the award winners and empty otherwise.

A sample dataset is available at `data/movielist.csv`.

## Running with Docker

```bash
docker compose up --build
```

The API is served at <http://localhost:8000>, with interactive documentation at
<http://localhost:8000/docs>.

The compose file mounts `data/movielist.csv` into the container. To load
another movie list, point `MOVIES_CSV` to the file on the host (and optionally
`API_PORT` to another host port):

```bash
MOVIES_CSV=/path/to/movies.csv API_PORT=8080 docker compose up
```

Without compose:

```bash
docker build -t golden-raspberry-awards-api .
docker run --rm -p 8000:8000 \
  -v /path/to/movies.csv:/data/movielist.csv:ro \
  golden-raspberry-awards-api
```

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

MOVIES_CSV_PATH=data/movielist.csv uvicorn app.main:create_app --factory --reload
```

The application refuses to start when `MOVIES_CSV_PATH` is missing or when the
file is invalid (the error message points to the offending line).

## Running the tests

```bash
pytest
```

All tests are integration tests: each one starts the application, imports a
CSV file and exercises the HTTP endpoints. Besides the sample movie list, the
suite builds alternative datasets to check ties, repeated producers, shared
credits, same-year awards and empty results.

Lint and formatting checks:

```bash
ruff check .
ruff format --check .
```

## API

All routes are read-only and live under `/api/v1`. The API follows level 2 of
the Richardson Maturity Model: resources are addressed by URI, accessed through
HTTP verbs and answered with meaningful status codes (`200`, `404`, `405`,
`422`).

| Method | Route                               | Description                                          |
|--------|-------------------------------------|------------------------------------------------------|
| GET    | `/api/v1/producers/award-intervals` | Producers with the shortest and longest award gap    |
| GET    | `/api/v1/movies`                    | Paginated nominees (`year`, `winner`, `limit`, `offset`) |
| GET    | `/api/v1/movies/{id}`               | A single nominee                                     |

### Award intervals

```bash
curl http://localhost:8000/api/v1/producers/award-intervals
```

```json
{
  "min": [
    {"producer": "Joel Silver", "interval": 1, "previousWin": 1990, "followingWin": 1991}
  ],
  "max": [
    {"producer": "Matthew Vaughn", "interval": 13, "previousWin": 2002, "followingWin": 2015}
  ]
}
```

Rules:

- Only movies flagged as winners count as awards.
- Credits are split into individual producers and studios on commas, `&` and
  the word `and`, in any case (`"A, B AND C"`, `"A & B"`, `"A, B, and C"`).
  Names that merely contain "and" (e.g. `Anderson`) are not split.
- Each producer/studio is identified by a slug that ignores case, spacing,
  accents and punctuation, so `Joel Silver`, `JOEL  SILVER` and `joel silver`
  are the same producer. The best-cased spelling is the one returned.
- Only **consecutive** awards of the same producer are compared.
- Every interval tied for the minimum (or maximum) is returned, so a producer
  may appear more than once and in both lists.
- Two awards in the same year produce an interval of `0`.
- When no producer has won more than once, both lists are empty.

### Movies

```bash
curl "http://localhost:8000/api/v1/movies?winner=true&limit=2"
```

```json
{
  "items": [
    {
      "id": 1,
      "year": 1980,
      "title": "Can't Stop the Music",
      "studios": ["Associated Film Distribution"],
      "producers": ["Allan Carr"],
      "winner": true
    }
  ],
  "total": 42,
  "limit": 2,
  "offset": 0
}
```

## Project layout

```text
app/
├── main.py            # application factory, startup import
├── core/config.py     # settings (environment variables)
├── db/session.py      # in-memory SQLite engine and sessions
├── routers/           # HTTP routes, delegate to the services
├── services/          # use cases and business rules, CSV import
├── repositories/      # data access (SQL queries)
├── models/            # SQLAlchemy ORM entities
└── schemas/           # Pydantic payloads returned by the API
tests/integration/     # end-to-end tests over HTTP
data/movielist.csv     # sample dataset
Dockerfile, docker-compose.yml
docs/                  # development notes
```

Requests flow `routers → services → repositories → models`. Routers only
translate HTTP into service calls and service errors into status codes;
business rules live in the services; SQL stays in the repositories. ORM models
and API schemas are kept apart so the database layout never leaks into the
public contract. Each layer is wired per request through FastAPI dependency
injection.

The award intervals are computed by the database with the `LAG` window function
partitioned by producer; the service layer only selects the extremes, keeping
the work linear in the number of awards.

## AI-assisted development

This project was built with an AI coding agent. The prompts and decisions are
recorded in [docs/ai-assisted-development.md](docs/ai-assisted-development.md).
