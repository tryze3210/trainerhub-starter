FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r /tmp/requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/app/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --create-home --gid app app

WORKDIR /app/backend

COPY --from=builder /wheels /wheels
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt \
    && rm -rf /wheels /tmp/requirements.txt

COPY --chown=app:app backend /app/backend
COPY --chown=app:app deploy/backend /app/deploy/backend
RUN chmod +x /app/deploy/backend/*.sh

USER app

EXPOSE 8000
CMD ["/app/deploy/backend/entrypoint.sh"]
