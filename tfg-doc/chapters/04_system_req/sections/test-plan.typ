// chapters/04_system_req/sections/test-plan.typ

The testing strategy is structured as a three-tier pyramid: unit tests at the
base, integration tests in the middle, and end-to-end tests at the top. Each
tier targets a different test object, operates at a different level of
abstraction, and is fully automated. The strict three-layer backend architecture
(controller → service → repository) was a deliberate design decision that
enables each tier to be exercised in isolation, satisfying @req:nfr-mnt-02.

=== Unit Tests

*Scope:* Service layer and Pydantic input schemas - the only locations where
business rules, validation logic, and domain algorithms reside.

*Tool:* pytest with `unittest.mock`. Repository dependencies are replaced with
mock objects, so no database or network access is required.

*Rationale:* Because services contain all business logic, testing them in
isolation provides the fastest and most targeted feedback. This tier is
particularly valuable for the numerical modules (simulation algorithms, analytics
computation, quasi-extinction Monte Carlo) where a logic error would propagate
silently through the HTTP layer and produce wrong results without triggering an
obvious failure.

=== Integration Tests

*Scope:* REST API endpoints - each endpoint is exercised from the HTTP request
through the service and repository layers to a real PostgreSQL database.

*Tool:* pytest with FastAPI's `TestClient` and a dedicated test database
instance. Tables are truncated between tests to guarantee isolation.

*Rationale:* Unit tests with mocked repositories cannot reveal ORM mapping
errors, broken SQL queries, wrong HTTP status codes, or missing authentication
and authorisation guards. Integration tests verify that all three layers compose
correctly and that the system behaves as specified when real data is persisted
and read back. This tier also verifies that state-dependent flows - visibility
transitions, ownership rules, async job lifecycle - produce the correct
observable outcomes across requests.

=== End-to-End Tests

*Scope:* The browser-facing user interface, covering the complete flow from user
interaction to rendered result.

*Tool:* pytest with Playwright driving the Python Shiny frontend.

The test suite supports two execution modes. In *mock mode* (used in CI), a
lightweight mock server stands in for the real API; no database is required and
the tests run reliably in any environment. In *real mode*, Playwright drives the
full running stack, providing final validation before deployment.

*Rationale:* Integration tests exercise the API contract but cannot detect
UI rendering problems, broken navigation, or frontend reactive binding failures.
End-to-end tests validate the acceptance criteria of user stories as an actual
user would experience them, and are the only tier that covers the gap between
a correct API and a correctly functioning interface.

=== Test Coverage and Automation

All three tiers are executed automatically in the CI pipeline on every push or
pull request to the main branch (@req:nfr-mnt-03, @req:nfr-dev-03). Unit tests
run first because they require no infrastructure. Integration tests follow using
a PostgreSQL service container. End-to-end tests run in mock mode for
reliability.

The following table summarises the mapping between testing tiers, test objects,
and the requirements they verify:

#figure(
  table(
    columns: (auto, auto, auto),
    align: left,
    table.header([*Tier*], [*Test object*], [*Requirements verified*]),
    [Unit],
    [Service layer, schemas],
    [@req:nfr-mnt-02, @req:nfr-sec-04],

    [Integration],
    [REST API endpoints, DB layer],
    [Functional requirements; @req:nfr-sec-04, @req:nfr-sec-05, @req:nfr-sec-06, @req:nfr-per-01, @req:nfr-per-02, @req:nfr-per-03, @req:nfr-avl-02],

    [End-to-end],
    [Browser UI, user flows],
    [@us:01 – @us:22, @req:nfr-usa-01],
  ),
  caption: [Test tier mapping],
) <tab:test-tiers>

=== Out of Scope

Load testing and formal usability testing fall outside the automated test suite.
Performance non-functional requirements (@req:nfr-per-01, @req:nfr-per-02,
@req:nfr-per-03) are verified through integration test timings and targeted
manual testing. The usability requirement @req:nfr-usa-03 (first-use task
completion within five minutes) is validated through a structured evaluation
session with representative users; the results are presented in the evaluation
chapter.
