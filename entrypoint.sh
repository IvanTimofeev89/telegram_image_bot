#!/bin/sh
alembic upgrade head
poetry run python main.py
