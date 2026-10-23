# AI-assisted development log

The project was developed with **Claude Code** (Anthropic, model Claude Opus 5.5)
running inside VS Code as a pair-programming agent. The agent read the
requirements and the dataset, proposed the design, wrote the code and the tests,
ran them, and created one commit per feature. Every step was reviewed before
moving on.

## Prompts

1. **Project brief** — "Build a REST API in Python with FastAPI backed by an
   in-memory SQLite database. Follow the attached requirements and dataset. Use
   clear, documented English code (PEP 8, PEP 257 docstrings), a layered
   architecture (models, controllers, services) and commit per feature."
2. **Requirements** — the agent read the specification and `movielist.csv`
   (206 rows, `;`-delimited, `winner` is `yes` or empty, producers written as
   `"A, B and C"`).
3. **Identity / repository** — "Create the project under `clones/`, configure
   git with my personal e-mail and commit by feature; I will provide the remote
   later."

## Agent workflow and decisions

| Step | What the agent did | Decision / rationale |
|------|--------------------|----------------------|
| Dataset analysis | Counted rows, winners and producer separators with shell commands. | Split names on `,`, `, and` and ` and `; strip and de-duplicate. |
| Data model | Normalized `movies`, `producers`, `studios` with association tables. | Lets the database answer producer queries directly. |
| Database | SQLAlchemy engine on `sqlite://` with `StaticPool`. | A single shared connection keeps the in-memory DB alive across requests. |
| Startup import | CSV loaded inside the FastAPI lifespan, one transaction. | Invalid files abort startup with the offending line number. |
| Bug found | Generated ids did not follow file order (cascade reordered inserts). | Add each movie to the session as soon as it is built. |
| Award intervals | `LAG(year) OVER (PARTITION BY producer ORDER BY year)` in SQL. | Only consecutive wins are compared; ties are all returned. |
| Edge cases | Same-year wins → interval `0`; no repeat winners → empty lists. | Documented in the README and covered by tests. |
| Validation | Results cross-checked against an independent script before writing the tests. | Expected: min Joel Silver 1990→1991, max Matthew Vaughn 2002→2015. |
| Tests | Integration tests only, through `TestClient`, with generated datasets. | Guards against different input data in production. |
| Tooling | `ruff` (PEP 8 + Google-style docstrings) and `pytest` run after each step. | Clean lint and 25 passing tests before each commit. |

## Commands run by the agent

```bash
uv venv .venv && uv pip install -e ".[dev]"
ruff format . && ruff check .
pytest -q
```
