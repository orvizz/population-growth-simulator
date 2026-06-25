// chapters/08_conclusions/index.typ

= Conclusions and Future Work

== Conclusions

=== Requirements Coverage

The functional requirements identified in @sec:stakeholder-requirements have all been
delivered: authentication (register @us:01, log in @us:02, log out @us:03) with secure
password storage; the COMPADRE and COMADRE matrix catalogue with browsing (@us:04),
search (@us:05), and export (@us:07), seeded automatically per @us:08; custom matrices
with full CRUD support (create @us:10, edit @us:11, delete @us:12), including, as of
this revision, complete editing of cell values and metadata (see the @us:11 note
below); visibility and sharing controls (@us:13, @us:14); deterministic and stochastic
simulations (@us:16, @us:17) with their associated ecological analytics (@us:20); and
asynchronous quasi-extinction analysis with per-stage threshold configuration
(@us:21, @us:22). The non-functional
goals stated in Chapter 1 (@sec:general-description, a web-based, zero-installation tool, freely accessible to
students and researchers regardless of institution) are also met: the application
requires only a browser, and is deployed publicly with no account needed to browse the
catalogue or run an ephemeral simulation.

One requirement was delivered later than the others. @us:11 ("edit the cell
values and metadata of a custom matrix I own") had its backend fully implemented and
tested from early on, but the frontend only exposed `common_name` and `country_code`
for editing (species, kingdom, matrix cell values, and stage names were not editable
through the UI), despite the acceptance criteria requiring it. This was found during the documentation
phase, while auditing the user stories against the live application, and fixed with the
same test-driven discipline used elsewhere in the project: failing unit tests for the
extracted shared grid-editor module, then failing end-to-end tests for the full edit
flow, before writing the implementation. It is a useful case study in why specifying
acceptance criteria is not the same as verifying them.

=== Technical Lessons

The strict controller → service → repository layering proved its value most clearly in
testing: every service can be unit-tested against mocked repositories with no database
required, which kept the unit suite (@tab:unit-test-results, 249 tests) running in seconds and made it the
natural place to put business-rule tests. FastAPI's automatic OpenAPI generation and
Pydantic's validation caught contract mismatches early and gave the frontend a reliable,
self-documenting API to build against. Python Shiny enabled a fully reactive UI without
a separate JavaScript build step, which suited a solo-developer timeline well, though
it comes with real constraints: the US-11 fix above surfaced a subtle Shiny pitfall
(reading and writing the same reactive value within one render execution creates a
self-invalidation loop), and a second bug where a parent container re-render silently
discarded a child output's pending update, both invisible without end-to-end browser
testing. Unit and integration tests alone would not have caught either.

=== Interdisciplinary Dimension

Implementing the analytics service required engaging directly with population ecology
literature, eigenvalue-based metrics (dominant growth rate, stable stage
distribution, reproductive value, sensitivity and elasticity) come from
@caswell2001, and the quasi-extinction threshold concept from
@quantitative-conservation-biology. Integrating the COMPADRE and COMADRE databases
exposed practical data-wrangling challenges (heterogeneous matrix dimensions, missing
values, and an R-native `.RData`/JSON distribution format that needed careful, defensive
parsing). This collaboration between the School of Engineering and the Faculty of
Biology is the project's defining characteristic, and shaped technical decisions (such
as keeping COMPADRE/COMADRE matrices read-only and immutable in stored simulations)
that a purely software-engineering brief would not have surfaced on its own.

=== Process Reflection

Containerisation with Docker Compose eliminated environment-specific bugs almost
entirely; the one exception, the `entrypoint.sh` CRLF issue (risk @tab:risk-t-06,
materialised early and resolved quickly), was itself an argument for containerising
sooner rather than later. The CI/CD pipeline (unit and integration tests, Bandit, pip-audit, Trivy,
CodeQL, soon SonarCloud) made it possible to merge with confidence throughout
development. Test-driven development was not applied with full consistency in the
earliest implementation sprints, which is part of why the @us:11 gap went undetected for
as long as it did; the fix applied strict red-green-refactor discipline throughout, and
that contrast is itself a useful, concrete lesson about the cost of skipping it.

== Future Work <sec:future-work>

Several items that were originally scoped as future work during earlier planning
(COMADRE seeding, internationalisation (@us:24), average-matrix display for stochastic
and quasi-extinction runs, per-stage quasi-extinction thresholds and exclusion
(@us:22), and the per-run-commitment stochastic simulation rework) have since been
fully implemented and shipped, and are described in their respective chapters rather
than here. What remains:

- *Real-time collaboration*: concurrent editing of the same matrix by multiple users is
  explicitly out of scope (@sec:stakeholder-requirements) and would require optimistic
  concurrency control or operational transforms not currently designed for.
- *Celery/Redis migration*: quasi-extinction jobs currently run as FastAPI
  `BackgroundTasks` against a DB-backed `SimulationJob` record. The architecture was
  designed with this migration in mind (job state already lives in the database, not in
  process memory), but moving to a proper task queue would be needed to support many
  concurrent users running Monte Carlo analyses at once.
- *Observability infrastructure*: as noted in @sec:dashboards, Prometheus metrics
  collection and Grafana dashboards were deliberately left out of the current release
  (observability today is limited to Uvicorn's structured access logs and the `/health`
  liveness probe). Adding a Prometheus exporter (e.g.
  `prometheus-fastapi-instrumentator`), a scrape configuration, and Grafana dashboards
  for request latency, error rate, and quasi-extinction job throughput would matter most
  if the institutional-deployment item below materialises and the application starts
  serving concurrent classroom-scale traffic.
- *Faster first-deploy seeding*: seeding the full COMPADRE and COMADRE catalogue
  (~18,000 records, @sec:railway-operations) takes 2-3 minutes on first deploy, during
  which the API does not respond. A pre-baked database image or a lazy/background
  seeding strategy would remove this cold-start cost.
- *Institutional deployment*: the application is already publicly deployed
  (@sec:railway-deployment), but formal adoption into a Biology course's curriculum
  (with instructor accounts, classroom-scale usage, and direct faculty feedback) has
  not yet happened and remains the project's original long-term goal.
