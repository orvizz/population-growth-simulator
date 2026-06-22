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
Probability-Impact Matrix (@tab:pi-matrix) -- green, yellow, or red.

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
threats (@sec:risk-mgmt-plan) also classify *opportunities* -- positive risks: events
that would benefit the project if they occur. Six opportunities were identified across
the four RBS categories, analysed the same way as the risks above, with the exposure
score determining the opportunity's zone on the Opportunity Probability-Impact Matrix
(@tab:opp-pi-matrix). Strategy follows the PMBOK opportunity responses -- Exploit,
Enhance, Share, or Accept -- in place of the threat responses Avoid, Mitigate,
Transfer, or Accept.

#include "opportunities.typ"

==== Opportunity Register

@tab:opportunity-register summarises all identified opportunities. The one
red-zone opportunity (@tab:opportunity-opp-e-01) has a dedicated exploitation plan in
@sec:risk-mgmt-plan, to be activated if the opportunity arises.

#opportunity-register-table

=== Initial Budget

==== Cost Budget

#guia[Detailed estimation of the internal costs of the project.]

==== Client Budget

#guia[This section will be included when required.]

== Project Execution

=== Planning Tracking Plan <sec:tracking-plan>

#guia[Explanation of the tracking plan. At least the description of 3 baselines should
be introduced (initial, mid-project, and final).]

#include "sprints/tracking.typ"

=== Project Issue Log

#guia[Ideally, relate it to the planning update.]

=== Risks

#guia[Follow-up of at least 5 risks. Include the risk sheets. Ideally, relate the
events in the issue log to the occurrence of risks if they appear.]

== Project Closure

=== Final Planning

=== Final Risk Report

=== Final Cost Budget

=== Lessons Learned


#pagebreak(weak: true)