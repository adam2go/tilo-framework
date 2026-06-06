FROM python:3.12-slim

WORKDIR /app

COPY backend/pyproject.toml backend/README.md ./
# The Docker stack runs the full server against Postgres.
RUN pip install --no-cache-dir ".[server,postgres]"

COPY backend/tilo ./tilo
COPY examples ./examples

EXPOSE 8000
CMD ["uvicorn", "tilo.main:app", "--host", "0.0.0.0", "--port", "8000"]
