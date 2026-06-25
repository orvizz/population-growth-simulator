// chapters/03_stakeholder_req/index.typ
#import "../../template.typ": guia, req, req-group

= Stakeholder Requirements

// #guia[The purpose is to provide an initial definition of the requirements for a system
// that can provide the services needed by users and other stakeholders. This involves a
// preliminary description of what the system to be developed should include.

// As a guideline, the content of this chapter corresponds to the results of the
// "Stakeholder Requirements Definition" process in ISO/IEC 15288 or the "System
// Feasibility Study (EVS)" process in the Métrica Version 3 methodology.]

== System Scope

The system is a *web-based population dynamics simulation platform*, accessible from
any modern browser, aimed at biology researchers and students who work with
stage-structured demographic matrix models. It encompasses:

- A REST API backend (FastAPI) that manages user accounts, population matrices,
  simulation runs, and asynchronous analytics jobs.
- A web frontend (Python Shiny) providing an interactive interface for browsing the
  matrix catalogue, running simulations, and managing custom matrices.
- A PostgreSQL database pre-seeded with the COMPADRE Plant Matrix Database and COMADRE animal database
  (approximately 18,000 matrices), alongside user-created custom matrices.
- A CI/CD pipeline (GitHub Actions, @sec:cicd) for automated testing and security scanning.

*Out of scope* for this project:

- Native mobile applications.
- Real-time collaboration (concurrent editing of the same matrix by multiple users),
  identified as future work (@sec:future-work).
- Automatic re-synchronisation with COMPADRE (seeding is a one-time operation
  performed at container build/start time).

== Stakeholder Requirements <sec:stakeholder-requirements>

// #guia[This will include the identified requirements, usually organized in a structured
// way using a hierarchical list. It will address both functional and non-functional
// requirements and other constraints that condition the final product. Note that these
// requirements should be written from the user's point of view and must be brief and
// concise. As a guideline, they may occupy two or three pages.]

#include "requirements.typ"

=== System Constraints

System constraints are restrictions imposed on the solution from outside the
development team; they are not design choices but fixed conditions that any
acceptable solution must satisfy.

#req-group("SR-C")

#req("Programming Language", [
  All application components (backend, frontend, and data-access layer)
  shall be implemented in Python. This constraint was mandated by the Biology
  Faculty tutor to ensure long-term maintainability by the research group.
])

#req("Frontend Framework", [
  The user interface shall be built using the Python Shiny framework. The
  choice of framework was explicitly specified by the Biology Faculty tutor
  and is not open to substitution.
])

#req("Matrix Data Source", [
  The system shall pre-seed its population matrix catalogue exclusively from
  the COMPADRE Plant Matrix Database and the COMADRE Animal Matrix Database.
  No alternative or supplementary matrix source is within scope.
])

#req("Delivery Format", [
  The system shall be delivered as a web application accessible from any
  standard modern browser. Native desktop and native mobile applications are
  explicitly out of scope.
])

#req("Legal and Regulatory Compliance", [
  The system shall comply with all applicable regulations: the General Data
  Protection Regulation (GDPR) and its Spanish transposition (LOPD-GDD) for
  personal data protection, the Intellectual Property Law (LPI), and the Law
  on Information Society Services and Electronic Commerce (LSSICE).
])

== Alternatives

// #guia[When there is freedom to choose between several alternatives (both functional
// and technical) to comply with the user requirements, a description of their pros and
// cons and the justification for the selected alternative should be included.]

This section is divided into two subsections: "Solution Alternatives" and "Technology Alternatives". The former describes the different solutions presented for this project (web app, desktop app (with Python or with a `.exe` file), a python script or Jupyter notebook...). 

The latter describes the different technical alternatives considered to build the project, the selected programming language (Python) for the frontend (used Python Shiny as a constraint from the stakeholder), backend (FastAPI), the database selection (relational Postgres database), the migration technology, and the ORM used.



#include "alternatives/solution_alternatives.typ"

#include "alternatives/technology_alternatives.typ"
