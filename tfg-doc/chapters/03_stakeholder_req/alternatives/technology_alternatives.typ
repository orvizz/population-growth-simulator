#import "../tables.typ": backend-comparison-table, database-comparison-table

=== Technology Alternatives

Every technology decision in this project was made deliberately, with concrete alternatives
evaluated and rejected for specific reasons. This section documents that process for the
six most consequential choices: programming language, frontend framework, backend framework,
database, ORM, and migration tooling.

==== Programming Language — Python

The project requires three distinct capabilities from a single codebase: numerical matrix
operations at the core of the simulation engine, a REST API serving JSON over HTTP, and a
reactive graphical interface. The choice of programming language had to satisfy all three
without forcing the use of multiple languages with separate runtimes, toolchains, and
dependency trees.

*R* @rlang was the first alternative considered given the project's roots in population ecology.
R has a strong statistical computing ecosystem and its own Shiny framework for reactive
web applications. However, R's production web server story is fragile — `plumber` APIs
are rarely deployed outside of data science teams, and combining R with a relational
database, a REST API, and a persistent user system requires bridging to tools that are
not idiomatic in the language. The result would be an unusual and hard-to-maintain stack.

*Node.js / TypeScript* @nodejs is the dominant choice for REST APIs and single-page applications
and would have produced an excellent backend. However, it has no equivalent to NumPy for
matrix algebra. Population projection matrices require efficient n-dimensional array
operations backed by optimised BLAS routines; implementing these from scratch in JavaScript
is neither practical nor appropriate. A hybrid approach — TypeScript API, Python
microservice for simulation — would reintroduce cross-language complexity and split the
codebase.

*Java / Kotlin* provides robust concurrency and mature API frameworks (Spring Boot,
Quarkus), but brings heavyweight tooling, verbose boilerplate, a JVM runtime requirement,
and no first-class scientific computing ecosystem. The NumPy problem remains unsolved.

Python @python resolves all three requirements simultaneously. NumPy @numpy provides BLAS-backed matrix
multiplication natively; FastAPI and Python Shiny handle the API and UI within the same
runtime; and the entire stack can be managed with a single `requirements.txt`. Python 3.13
was chosen specifically for its interpreter performance improvements and because it matches
the version available in the GitHub Actions CI runner.

==== Frontend Framework — Python Shiny

The use of Python for the frontend was a stakeholder constraint set by the Biology Faculty
tutor. Within that constraint, three Python-native alternatives to Python Shiny were
evaluated.

*Streamlit* @streamlit has an exceptionally low learning curve and is the most popular choice for
rapid data prototyping. Its rendering model, however, re-runs the entire script on every
interaction — a limitation that makes fine-grained state management for multi-step
workflows (parameter configuration, simulation run, result inspection) require fragile
session-state workarounds. Its layout system defaults to a single column, making a
multi-tab application with a sidebar and a chart panel awkward to build.

*Dash* @dash (Plotly) is purpose-built for data dashboards and integrates naturally with Plotly
charts. As the number of reactive components grows, its callback graph becomes difficult
to reason about; every input-to-output relationship must be declared explicitly, and
circular dependencies or missing callbacks produce runtime errors that are hard to trace.
Its layout is defined in verbose Python dict-style HTML, which produces more code than UI.

*FastAPI with Jinja2 templates* would give full control over the HTML and CSS, but any
interactive behaviour beyond a form submission requires JavaScript — directly contradicting
the stakeholder's constraint and splitting the frontend into two languages.

The reactive programming model of Python Shiny @shiny — where output functions automatically re-execute
when their declared inputs change — maps cleanly onto the application's interaction pattern:
a set of simulation parameters driving a live population chart. The framework keeps all UI
logic in Python, integrates naturally with NumPy arrays and matplotlib figures, and produces
a responsive single-page experience without requiring JavaScript knowledge.

==== Backend Framework — FastAPI

With Python chosen as the language, three web frameworks were evaluated for the REST API:
FastAPI @fastapi, Flask @flask, and Django REST Framework @drf.

*Flask* is the most minimal of the three. It provides routing and a request/response cycle
and nothing else, which means that everything the API needs — input validation, schema
serialisation, OpenAPI documentation, and async support — must be assembled from separate
third-party packages (marshmallow or pydantic-flask, flask-smorest, and eventually a WSGI
→ ASGI adapter). For an API with well-defined contracts and a strict layered architecture,
this assembly cost is unnecessary overhead that Flask's flexibility does not justify.

*Django REST Framework* is comprehensive and production-proven. Its built-in ORM,
authentication system, admin panel, pagination, and browsable API cover a wide range of
use cases. However, Django's ORM is tightly coupled to Django @django itself: using SQLAlchemy
alongside Django creates a dual-ORM situation where migrations, session management, and
model definitions are controlled by two separate systems. SQLAlchemy is a hard requirement
here because Alembic — the chosen migration tool — depends on it directly, and the
repository pattern in the service layer relies on SQLAlchemy sessions. Beyond the ORM
conflict, Django's template engine, admin interface, and full-stack conventions are unused
weight for a headless API whose only output is JSON.

FastAPI resolves both problems. It generates a live Swagger UI at `/docs` automatically
from the route and schema definitions, with no additional packages. Input validation and
response serialisation are declared as Pydantic v2 @pydantic model classes, which FastAPI validates
and serialises natively and efficiently (Pydantic v2's Rust-backed core is substantially
faster than its predecessor). The framework is async-first, built on Starlette @starlette, leaving
the door open for non-blocking I/O without a rewrite. Its dependency injection system
(`Depends`) maps directly onto the controller → service → repository architecture: a DB
session, a service instance, and the authenticated user are all resolved and injected per
request with a few lines of code in `api/deps.py`. Finally, FastAPI imposes no ORM
preference, integrating with SQLAlchemy without conflict.

#backend-comparison-table

==== Database — PostgreSQL

The data model has an unusual characteristic: several columns store structured,
variable-length nested data (the population matrix components `matrix_a`, `matrix_u`,
`matrix_f`; the simulation trajectory `result_history`; the list of stage labels
`stage_names`; and the stochastic matrix index array `matrix_ids`). At the same time,
the model relies on relational integrity — foreign keys from `simulation_runs` to
`population_matrices`, unique constraints on `users.username` and `users.email`, and
transactional guarantees when a simulation record is created alongside its metadata.
This combination is the key constraint that drove the database decision.

*MySQL / MariaDB* @mysql is a mature, widely-deployed relational database with comparable
performance characteristics to PostgreSQL. However, it does not provide a native JSONB
type. Storing variable-length nested structures would require TEXT columns with manual
serialisation, losing the ability to index or query into nested fields, or a hybrid
approach that offloads document-shaped data to a separate store — reintroducing the
complexity that a single unified database is meant to avoid.

*SQLite* @sqlite is the natural choice for local development: zero configuration, a single file,
and full SQLAlchemy compatibility. It is, however, unsuitable for the production use case.
SQLite's write concurrency model uses file-level locking, which serialises all write
operations and degrades severely under simultaneous requests from multiple users. It also
has no native JSONB type and no production-grade connection pooling.

*MongoDB* @mongodb stores documents natively, which would handle the variable-length matrix columns
elegantly without any schema overhead. The trade-off is the loss of the relational
guarantees that the rest of the data model depends on: there are no enforced foreign keys,
no multi-document transactions in the free tier, and no straightforward equivalent to the
unique constraints on user credentials. SQLAlchemy's MongoDB support is provided through a
separate ODM rather than the standard ORM interface, complicating the repository pattern
and the Alembic migration workflow.

PostgreSQL @postgresql provides both capabilities in a single engine. Its native JSONB type stores
nested structures as binary-indexed JSON, allowing efficient querying into nested fields
while preserving full relational integrity around them. Version 16 introduces further
performance improvements to parallel query execution and JSONB handling that are directly
relevant to the query patterns of this application — particularly list queries that filter
across both relational columns and JSONB metadata fields.

#database-comparison-table

==== ORM — SQLAlchemy

Three approaches to database access were evaluated: Django ORM, Tortoise ORM, and raw
SQL via `psycopg2`.

*Django ORM* @django was excluded together with Django REST Framework. Using Django's ORM outside
of a Django application requires pulling in the entire framework to initialise the ORM's
application registry, which creates lifecycle and configuration conflicts with FastAPI's
request handling.

*Tortoise ORM* @tortoise is an async-native ORM designed specifically for use with FastAPI and
ASGI frameworks. Its API is clean and Pythonic. However, it is a younger project with a
smaller ecosystem, and — critically — Alembic, the de-facto standard for SQLAlchemy
migrations, does not support Tortoise ORM. Adopting Tortoise ORM would require either
a different migration tool (none of which offer `--autogenerate` from model diffs as
cleanly as Alembic) or managing migrations manually.

*Raw SQL via psycopg2* @psycopg2 offers maximum control and the lowest query overhead. The cost is
that query logic becomes tightly coupled to the database schema; any schema change requires
manually updating every affected query string. More importantly for the test strategy,
raw SQL queries cannot be replaced with `unittest.mock.MagicMock` objects — the entire
test suite would require a live database connection, making fast, isolated unit tests
impossible.

SQLAlchemy @sqlalchemy uses a declarative mapping style that keeps model definitions
readable and co-located with Python type annotations. Its session model integrates with FastAPI's `Depends`
injection with a single generator function, scoping each session to the lifetime of a
single HTTP request. ORM objects returned by repository methods can be replaced wholesale
with `MagicMock` instances in unit tests, enabling the service layer to be tested in
complete isolation from the database. This is the foundation of the two-speed test
strategy described in the design chapter.

==== Database Migrations — Alembic

Three alternatives to Alembic were considered for managing schema evolution.

*Django migrations* are excluded together with Django ORM — they are not usable outside
the Django framework.

*Flyway* @flyway and *Liquibase* @liquibase are JVM-based migration tools with strong track records in
enterprise Java projects. Both require a separate Java runtime installed alongside the
Python application — a significant operational dependency for a Python-only stack.
Neither tool has the ability to introspect SQLAlchemy model definitions and auto-generate
migration scripts from model diffs, which means every migration must be written by hand
in SQL.

*Manual SQL scripts* give the developer complete control over every DDL statement and
avoid any migration framework entirely. The cost is the absence of versioning, rollback
paths, drift detection, and the guarantee that the running code and the database schema
are in sync. In a containerised deployment where the schema must be updated before the
application starts, manual scripts require a custom orchestration layer that Alembic
provides out of the box.

Alembic @alembic is the direct companion library to SQLAlchemy and requires no integration work.
It generates migration scripts automatically by comparing the current SQLAlchemy model
definitions against the database schema (`alembic revision --autogenerate`), versions
them sequentially in `alembic/versions/`, and applies them idempotently at container
startup via `entrypoint.sh` (`alembic upgrade head`). Two migrations exist in the
current codebase: `0001_initial_schema`, which creates the `users` and
`population_matrices` tables, and `0002_simulation_runs`, which adds the `simulation_runs`
table with its stochastic columns. Both run automatically on every container start,
ensuring the database schema is always in sync with the deployed code without any manual
intervention.
