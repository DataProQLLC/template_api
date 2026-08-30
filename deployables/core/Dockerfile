# services/core/Dockerfile
FROM python:3.11.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Create the runtime user up front; we drop to it after installing.
RUN useradd --create-home --uid 1000 app

# Dependencies first. This layer stays cached until requirements.txt changes.
COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /srv/requirements.txt

# Application code second, so editing a route doesn't reinstall 29 packages.
COPY shared/ /srv/shared/
COPY services/core/app/ /srv/app/

RUN chown -R app:app /srv
USER app

EXPOSE 8080
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}