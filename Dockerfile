FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MOVIES_CSV_PATH=/data/movielist.csv

WORKDIR /srv

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install . \
    && useradd --system --no-create-home api

# Default dataset; replace it by mounting another file on the same path.
COPY data/movielist.csv /data/movielist.csv

USER api
EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
