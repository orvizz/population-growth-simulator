#!/bin/sh
set -e

echo "Applying database migrations..."
python -m alembic upgrade head

# Seed COMPADRE data if not already present
COMPADRE_COUNT=$(python -c "
from db.session import SessionLocal
from db.models import PopulationMatrix
with SessionLocal() as s:
    print(s.query(PopulationMatrix).filter(PopulationMatrix.source_type == 'compadre').count())
")

if [ "$COMPADRE_COUNT" = "0" ]; then
    echo "No COMPADRE rows found — seeding COMPADRE data..."
    python -m db.seed_compadre
else
    echo "COMPADRE already has $COMPADRE_COUNT rows — skipping."
fi

# Seed COMADRE data if not already present
COMADRE_COUNT=$(python -c "
from db.session import SessionLocal
from db.models import PopulationMatrix
with SessionLocal() as s:
    print(s.query(PopulationMatrix).filter(PopulationMatrix.source_type == 'comadre').count())
")

if [ "$COMADRE_COUNT" = "0" ]; then
    echo "No COMADRE rows found — seeding COMADRE data..."
    python -m db.seed_comadre
else
    echo "COMADRE already has $COMADRE_COUNT rows — skipping."
fi

echo "Starting server..."
exec "$@"
