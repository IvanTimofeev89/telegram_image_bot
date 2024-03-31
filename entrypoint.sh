#!/bin/sh
alembic revision --autogenerate
alembic upgrade head
poetry run python main.py
