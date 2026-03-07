= Database Design <database>

== Schema Overview

The database contains three tables managed by SQLAlchemy ORM models defined in
`db/models.py`. @fig-er shows the entities, their attributes, and the
foreign-key relationships between them.

#figure(
  image("../diagrams/er.svg"),
  caption: [Entity-relationship diagram],
) <fig-er>

== Entity Details

=== `users`

Stores registered user accounts. Passwords are stored as bcrypt hashes; the
plaintext password is never persisted. The `username` and `email` columns carry
unique constraints enforced at the database level as a second line of defence
after the service-layer check.

=== `population_matrices`

The central reference entity. Two kinds of records coexist in this table,
distinguished by `source_type`.

*COMPADRE matrices* (`source_type = "compadre"`) are seeded from the COMPADRE
Plant Matrix Database at startup. They have `owner_id = NULL` and are
read-only; any attempt to modify them through the API is rejected with `403
Forbidden`. The `metadata_` column stores COMPADRE-specific fields (e.g.
`MatrixID`, `StudyDuration`) as a JSONB object.

*Custom matrices* (`source_type = "custom"`) are created by authenticated
users through `POST /v1/matrices`. They are owned by the creating user
(`owner_id` is set to the user's id) and can be updated or used in
simulations.

The ORM column is named `metadata_` (with a trailing underscore) to avoid
a name collision with SQLAlchemy's internal `metadata` attribute. The API
serialises it as `"metadata"` through a Pydantic `validation_alias`.

=== `simulation_runs`

Records a complete simulation result including every vector in the trajectory.
The `result_history` JSONB column stores the full list of population vectors
from step 0 (the initial vector) to step `n_steps`, inclusive. This makes
retrieval of individual runs self-contained without re-running the algorithm.

For deterministic runs, `matrix_id` is set and `matrix_ids` is null. For
stochastic runs, `matrix_ids` is set (as a JSONB array of integers) and
`matrix_id` is null. The `random_seed` column enables exact reproduction of
stochastic runs.

The `stage_names` column is a snapshot of the stage labels at run time. This
ensures that historical simulations remain interpretable even if the source
matrix is later updated.

== Migrations

Schema evolution is managed by Alembic. Each migration is a versioned Python
script in `alembic/versions/` containing `upgrade()` and `downgrade()`
functions. The current migration chain is:

```
0001_initial_schema.py  — users, population_matrices
0002_simulation_runs.py — simulation_runs with stochastic columns
```

Migrations are applied automatically by `entrypoint.sh` before the API server
starts:

```bash
python -m alembic upgrade head
```

Running `alembic upgrade head` is idempotent; already-applied migrations are
skipped. This guarantees that the schema is always up to date when the
container starts, without any manual intervention in any environment.

To generate a new migration after modifying `db/models.py`:

```bash
python -m alembic revision --autogenerate -m "description"
```

Alembic compares the current ORM model definitions against the live schema and
generates the necessary `ALTER TABLE` statements automatically.

== COMPADRE Seeding

`db/seed_compadre.py` populates the `population_matrices` table with real
population projection matrices from the COMPADRE database. The seeder is
called by `entrypoint.sh` immediately after migrations complete. It is
idempotent — it checks for existing COMPADRE records before inserting — so
restarting the container does not duplicate data.

COMPADRE matrices provide users with a ready-made set of ecologically validated
matrices to explore and use in simulations without needing to create their own.
