# Docker

## `docker/Dockerfile`
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -U pip

COPY pyproject.toml /app/pyproject.toml
COPY tests /app/tests
#RUN pip install --no-cache-dir .
COPY app /app/app
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir ".[dev]"
#COPY README.md /app/README.md
#COPY .env.example /app/.env.example

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
