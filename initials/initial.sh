#! /usr/bin/env bash

# Initialize database
python initials/db_starter.py

# Run migrations
alembic upgrade heads

# Create initial data
python initials/initial_data.py

# Run tests
# pytest --verbose --disable-warnings -vv -x --timeout=10

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 