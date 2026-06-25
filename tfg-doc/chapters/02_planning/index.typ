// chapters/02_planning/index.typ
#import "../../template.typ": guia
#import "tables.typ": stakeholders-table, system-users-table, obs-nodes-table, raci-table, risk-register-table, opportunity-register-table
#import "obs_diagram.typ": obs-diagram

= Planning and Management

#guia[This section is COMPULSORY. You must follow the guidelines provided by the
4th-year subject "Project Management and Planning" to develop a plan that details the
project activities, participants, timelines, and responsibilities for each, the
expected results, and the work plan to be followed for your TFG.

When preparing the planning and budget, keep in mind that there will be several tasks
parallel to the project's creation: Documentation, Testing, Project Management...
these must be reflected in the planning to achieve a better representation of the work
actually performed. Also, note that the different roles the student will occupy
(analyst, developer...) do not have the same cost in the budget. You should consider
assigning a different cost according to the role occupied by the student in each
planned phase.

For the planning, a Gantt chart must be included that allows all high-level tasks,
their duration, and interrelationships to be seen on a single page. If you wish to
show more detail, partial diagrams can be made.

In the case of using agile methodologies, the Gantt chart may show the different
iterations (sprints and/or releases) and other additional activities (e.g., training,
previous studies, documentation...). It can be accompanied by a summary story mapping
to show more detail. If time tracking has been performed, include the Burn-Down Chart.

This is the advisable content structure, but it is recommended that, at a minimum,
there is an initial plan, a risk list, an initial budget, and a final plan and budget.]

== Project Planning

=== Identification of Stakeholders

#guia[Since this was already detailed in a previous section, reference it here.]

The following table shows, identified by a unique ID and classified into external and
internal, the different stakeholders identified for the system "Population growth
simulator. Simulation of population models with stochasticity"

#stakeholders-table

==== System users

The following table shows the different types of users that are expected to interact
with the future system:

#system-users-table

=== OBS and PBS

In this section, I will present the organizational breakdown structure and the product
breakdown structure for this project.

==== OBS

This section defines the *Organizational Breakdown Structure (OBS)* for a project in
which one person performs all tasks, supported by two tutors who provide guidance,
feedback, and formal acceptance.

#obs-diagram

#obs-nodes-table

#raci-table

=== Initial Planning. WBS

This project was developed following the *Scrum* agile framework. Work was organised
into five development sprints plus an initial inception sprint, each lasting two to
three weeks. @tab:sprints summarises the sprint structure, goals, and durations.

#figure(
  table(
    columns: (auto, auto, auto, 1fr),
    stroke: 0.5pt + luma(180),
    align: (left + horizon, center + horizon, center + horizon, left + horizon),
    table.header(
      [*Sprint*], [*Period*], [*Duration*], [*Goal*],
    ),
    [Sprint 0], [Feb 11-28, 2026], [2.5 weeks],
      [Project inception: scope definition, Typst documentation template, initial Shiny prototype.],
    [Sprint 1], [Mar 1-14, 2026], [2 weeks],
      [Core architecture: FastAPI backend, PostgreSQL database, JWT authentication, COMPADRE seeder, initial test suite.],
    [Sprint 2], [Mar 15-28, 2026], [2 weeks],
      [MVP polish: matrix ownership model, frontend redesign, end-to-end tests, CI/CD pipeline setup.],
    [Sprint 3], [Mar 29 - May 8, 2026], [~5 weeks],
      [Component decoupling and TFG documentation foundation: architecture diagrams, requirements analysis, technology alternatives.],
    [Sprint 4], [May 9-26, 2026], [2.5 weeks],
      [Analytics service, quasi-extinction service, jobs system, simulation export format v2.],
    [Sprint 5], [May 27 - Jun 9, 2026], [2 weeks],
      [Feature completion: stochastic simulation, internationalisation, matrix import/export, comprehensive test suite.],
  ),
  caption: [Sprint overview],
) <tab:sprints>

The Gantt chart below (@fig:gantt) shows how the ten parallel workstreams overlap across
the project timeline. Blue cells indicate development activity; green marks testing and
DevOps work, which runs concurrently with most development sprints; orange marks the
documentation sprint that produced this document.

#include "gantt.typ"

#include "sprints/sprints.typ"

==== User Story Traceability

#include "traceability.typ"

=== Risks <sec:risks>

==== Risk Management Plan

Risk management for this project follows a Probability-Impact methodology adapted from
the PMBOK Guide: risks are classified by a four-branch Risk Breakdown Structure,
assessed against a qualitative probability scale and a four-objective (cost, schedule,
scope, quality) impact scale, and prioritised through a Probability-Impact Matrix. The
full methodology, scales, and the contingency plans for every red-zone risk are
described in @sec:risk-mgmt-plan.

==== Risk Identification

Thirteen risks were identified across the four Risk Breakdown Structure categories
(Technical, External, Organizational, and Project Management). Each risk below is
analysed using the scales defined in @sec:risk-mgmt-plan: probability is rated on a
five-level scale, impact is rated independently against cost, schedule, scope, and
quality, and the resulting exposure score (probability multiplied by the
worst-affected objective's impact) determines the risk's zone on the
Probability-Impact Matrix (@tab:pi-matrix), classified as green, yellow, or red.

#include "risks.typ"

==== Risk Register

@tab:risk-register summarises all identified risks. The five risks that fall in the
red zone (@tab:risk-t-01, @tab:risk-o-01, @tab:risk-o-02, @tab:risk-pm-01,
@tab:risk-pm-02) each have a dedicated contingency plan in @sec:risk-mgmt-plan, to be
triggered if the risk materialises.

#risk-register-table

=== Opportunities <sec:opportunities>

==== Opportunity Identification

The same Risk Breakdown Structure, probability scale, and impact scale used for
threats (@sec:risk-mgmt-plan) also classify *opportunities* (positive risks: events
that would benefit the project if they occur). Six opportunities were identified across
the four RBS categories, analysed the same way as the risks above, with the exposure
score determining the opportunity's zone on the Opportunity Probability-Impact Matrix
(@tab:opp-pi-matrix). Strategy follows the PMBOK opportunity responses (Exploit,
Enhance, Share, or Accept) in place of the threat responses Avoid, Mitigate,
Transfer, or Accept.

#include "opportunities.typ"

==== Opportunity Register

@tab:opportunity-register summarises all identified opportunities. The one
red-zone opportunity (@tab:opportunity-opp-e-01) has a dedicated exploitation plan in
@sec:risk-mgmt-plan, to be activated if the opportunity arises.

#opportunity-register-table

=== Initial Budget

#include "budget.typ"

==== Client Budget

#guia[This section will be included when required.]

== Project Execution

=== Planning Tracking Plan <sec:tracking-plan>

Progress was tracked against three baselines: the *initial* plan (Sprint 0, scope and
sprint structure as defined above), a *mid-project* checkpoint (end of Sprint 3, after
component decoupling and the start of TFG documentation), and the *final* baseline
(end of Sprint 5, feature-complete). The per-sprint tracking tables and @fig:burndown
below compare planned vs. actual duration and remaining points per sprint.

#include "sprints/tracking.typ"

=== Project Issue Log

Incidents encountered during development with a non-trivial resolution. None of these
blocked delivery for more than a few hours; all are also referenced from the relevant
risk in @sec:risk-mgmt-plan where applicable.

#figure(
  table(
    columns: (auto, 1fr, 1fr, 1fr),
    stroke: 0.5pt + luma(180),
    align: (left + top, left + top, left + top, left + top),
    table.header([*Date*], [*Issue*], [*Impact*], [*Resolution*]),
    [Sprint 1],
      [`entrypoint.sh` had CRLF line endings on Windows, breaking container startup],
      [Blocked all `docker compose up` runs on the development machine],
      [Converted to LF (`sed -i 's/\r//' entrypoint.sh`); documented in CLAUDE.md],
    [Sprint 1],
      [`httpx` was missing from `requirements.txt`],
      [Frontend container failed to start (import error)],
      [Added `httpx` to `requirements.txt`],
    [Sprint 1],
      [`docker-compose.yml` needed an explicit `POSTGRES_PORT: 5432` override, since `.env` holds the host-side port (5435)],
      [API container could not connect to the database],
      [Added a per-service port override in `docker-compose.yml`],
    [Sprint 2],
      [A Playwright E2E locator matched elements in both the create and edit matrix panels (e.g. a `.badge` text match)],
      [Flaky / blocked E2E test runs],
      [Scoped locators to the specific panel container (e.g. `#mm_edit_stage_tags .badge`)],
    [Sprint 2],
      [Integration tests were not isolated from the development database],
      [Test runs polluted local development data],
      [Added per-session `matrix_db_test` creation/teardown in `conftest.py`],
    [Documentation phase],
      [US-11 (@us:11, edit a custom matrix) was specified and the backend fully implemented it, but the frontend only exposed `common_name`/`country_code` for editing (species, kingdom, matrix cell values, and stage names were not editable)],
      [Acceptance criteria for a Must-priority user story were not actually met by the shipped feature],
      [Extracted a shared `matrix_grid.py` cell-grid editor, extended the edit form to full parity with the create form, added end-to-end test coverage],
    [Documentation phase],
      [Saving an edited matrix produced no visible confirmation, even though the save succeeded server-side (caused by `on_modified()` re-rendering the sidebar and recreating the edit panel's container before the scheduled confirmation message could attach to it)],
      [Edit flow appeared broken to the user despite working correctly],
      [Switched the success message to a toast notification (`ui.notification_show`), matching the pattern already used by the delete flow, which is unaffected by container recreation],
  ),
  caption: [Project issue log],
) <tab:issue-log>

=== Risks

Of the thirteen risks identified in @sec:risks, two materialised during execution:
*T-06* (@tab:risk-t-06, Windows/Linux environment inconsistency, the `entrypoint.sh` CRLF issue
above) and *PM-01* (@tab:risk-pm-01, schedule slippage, the requirements/technology research phase
and the frontend reactive-state implementation each ran roughly a week over estimate).
Both were absorbed using the schedule buffer without requiring scope reduction; neither
reached its contingency trigger. The remaining red-zone risks (O-01 / @tab:risk-o-01,
O-02 / @tab:risk-o-02, PM-02 / @tab:risk-pm-02) did
not materialise. Full risk sheets, including the contingency plans that would have been
triggered, are in @sec:risk-mgmt-plan.

== Project Closure

=== Final Planning

All five development sprints plus the inception sprint were completed; no planned
scope was cut. The documentation phase, originally scheduled as part of Sprint 5, ran
longer than planned and continued past the sprint boundary, which is the PM-01 risk
(@tab:risk-pm-01) above. @sec:tracking-plan shows the final planned-vs-actual comparison per sprint.

=== Final Risk Report

Two risks materialised (T-06 / @tab:risk-t-06, PM-01 / @tab:risk-pm-01, both described above); both were resolved without
invoking their formal contingency plans. No red-zone risk required schedule reserve
beyond ordinary buffer days. See @sec:risk-mgmt-plan for the full risk register and the
status of every individually tracked risk.

=== Final Cost Budget

The project was completed within the initial budget estimates. No scope
additions, emergency tooling purchases, or unplanned infrastructure costs
arose during the four-month development period. The two risks that
materialised (T-06 and PM-01, see @sec:risks) were absorbed within the
contingency reserve without requiring additional expenditure. The final
cost budget therefore matches @tab:budget-summary in its entirety.

=== Lessons Learned

- *Environment parity matters even for a solo developer*: the CRLF issue (T-06, @tab:risk-t-06) was the
  single largest source of early friction, entirely avoidable with an `.editorconfig`
  or a pre-commit hook (a concrete improvement identified too late to apply
  retroactively without risk to a stable pipeline).
- *Writing acceptance criteria does not guarantee they are met*: US-11's frontend gap
  went unnoticed for months because no automated test exercised the edit flow
  end-to-end, even though the backend was fully tested. The fix this pass came with
  full TDD discipline (failing unit and E2E tests written first) precisely because that
  gap was costly to discover late.
- *Buffer days are worth protecting*: both materialised risks (T-06, PM-01) were
  absorbed without schedule renegotiation only because buffer days existed and were not
  pre-allocated to other work.


#pagebreak(weak: true)