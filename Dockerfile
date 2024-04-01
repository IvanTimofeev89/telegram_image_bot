# BASE
FROM python:3.11-slim as base

# DEVELOPMENT
FROM base as development
ENV \
	PIP_NO_CACHE_DIR=off \
	PIP_DISABLE_PIP_VERSION_CHECK=on \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	VIRTUAL_ENV=/pybay-venv
ENV \
	POETRY_VIRTUALENVS_CREATE=false \
	POETRY_VIRTUALENVS_IN_PROJECT=false \
	POETRY_NO_INTERACTION=1 \
	POETRY_VERSION=1.8.2

# install poetry
RUN pip install "poetry==$POETRY_VERSION"

# copy requirements
COPY poetry.lock pyproject.toml ./

# add venv to path
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install python packages
RUN python -m venv $VIRTUAL_ENV \
	&& . $VIRTUAL_ENV/bin/activate \
	&& poetry install --no-root

# Porduction
FROM development as production
WORKDIR /app
COPY . .
RUN poetry install --without dev
# run script
ENTRYPOINT ["bash", "-c", "alembic upgrade head && python main.py"]