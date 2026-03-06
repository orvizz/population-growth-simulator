#!/bin/sh
set -e

echo "Applying database migrations..."
python -m alembic upgrade head

# Seed COMPADRE data on first run (when the table is empty)
ROW_COUNT=$(python -c "
from db.session import SessionLocal
from db.models import PopulationMatrix
with SessionLocal() as s:
    print(s.query(PopulationMatrix).count())
")

if [ "$ROW_COUNT" = "0" ]; then
    echo "population_matrices is empty — seeding COMPADRE data..."
    python -m db.seed_compadre
else
    echo "population_matrices already has $ROW_COUNT rows — skipping seed."
fi

echo "Starting server..."
exec "$@"
