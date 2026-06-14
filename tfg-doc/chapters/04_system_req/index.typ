// chapters/04_system_req/index.typ
#import "../../template.typ": guia, story-map

= System Requirements

#guia[These provide a technical representation or view of the required product,
indicating what it must do to fulfill the user requirements. This involves transforming
user requirements into a detailed system specification that satisfies the needs of
those users and serves as a basis for subsequent system design.

As a guideline, the content of this chapter corresponds to the results of the
"Requirements Analysis Process" in ISO/IEC 15288 or the "Information System Analysis
(ASI)" process in the Métrica Version 3 methodology.]

== Functional Requirements

#guia[As a general criterion, these requirements will be expressed through three
complementary views or models, each of which can be included as an independent section
as indicated below.]

=== System Functions

#guia[In most cases, this will be the most extensive part, and the way they are
represented will depend on the methodology used. For example, they can be represented
as use cases with their scenario descriptions, as user stories with their acceptance
criteria, or as a hierarchical list with detailed requirements.

NOTE 1: When using use cases, avoid redundant scenario descriptions that do not add
value (e.g., in simple CRUD operations, enumerating them might suffice without
including detailed scenarios).

NOTE 2: When using user stories + acceptance criteria, include a story mapping first
and organise the user stories according to it.]

==== Use Case Diagram

===== Overview

#figure(
  image("../../resources/diagrams/use-cases-overview.svg", height: 95%),
  caption: [Use Case Diagram — Overview (all actors and subsystems)],
) <fig:uc-overview>

===== Authentication

#figure(
  image("../../resources/diagrams/use-cases-auth.svg", width: 55%),
  caption: [Use Case Diagram — Authentication],
) <fig:uc-auth>

===== Browse Matrices

#figure(
  image("../../resources/diagrams/use-cases-browse.svg", width: 72%),
  caption: [Use Case Diagram — Browse Matrices],
) <fig:uc-browse>

===== Custom Matrices

#figure(
  image("../../resources/diagrams/use-cases-matrices.svg", width: 80%),
  caption: [Use Case Diagram — Custom Matrices],
) <fig:uc-matrices>

===== Simulations and Analytics

#figure(
  image("../../resources/diagrams/use-cases-simulations.svg", width: 85%),
  caption: [Use Case Diagram — Simulations and Analytics],
) <fig:uc-simulations>

===== Quasi-Extinction Analysis

#figure(
  image("../../resources/diagrams/use-cases-qe.svg", width: 60%),
  caption: [Use Case Diagram — Quasi-Extinction Analysis],
) <fig:uc-qe>

==== Use Case Descriptions

#include "sections/use-cases.typ"

// ==== Scenario Descriptions

// #include "sections/scenarios.typ"

==== Story Map

#figure(
  {
    set text(size: 6.5pt)
    story-map((
      (epic: "Authentication",       stories: ("Register", "Log in", "Log out")),
      (epic: "Browse Matrices",      stories: ("View catalog", "Filter", "View detail", "Export")),
      (epic: "Custom Matrices",      stories: ("Create", "Edit", "Delete", "Visibility", "Share", "Import")),
      (epic: "COMPADRE",             stories: ("Seed catalog", "Filter metadata", "Sim. source")),
      (epic: "Simulations",          stories: ("Determ. sim.", "Stoch. sim.", "Save run", "Browse runs", "Export/import")),
      (epic: "Analytics",            stories: ("Growth rate λ₁", "Stable distrib.", "Sensitivities")),
      (epic: "Quasi-Extinction",     stories: ("Start job", "Stage config.", "View results")),
      (epic: "Testing & DevOps",     stories: ("CI pipeline", "Sec. scanning", "Docker", "DB migrations")),
      (epic: "i18n",                 stories: ("Language sel.",)),
    ))
  },
  caption: [User Story Map],
) <tab:story-map>



==== User Stories

// Each story lives in its own file under stories/.
// Add new stories there and register them in stories/_index.typ.
#include "stories/_index.typ"



#include "sections/domain-data-model.typ"

#include "sections/ui.typ"


=== State Diagrams

In this section, I present some state diagrams that illustrate the behavior of some components of the application.

==== User Session

#figure(
  image("../../resources/diagrams/state-user-session.svg", width: 85%),
  caption: [State Diagram — User Session],
) <fig:sd-session>

==== Simulation Job

#figure(
  image("../../resources/diagrams/state-simulation-job.svg", width: 85%),
  caption: [State Diagram — Simulation Job (quasi-extinction async task)],
) <fig:sd-job>

==== Population Matrix

#figure(
  image("../../resources/diagrams/state-population-matrix.svg", width: 90%),
  caption: [State Diagram — Population Matrix visibility and lifecycle],
) <fig:sd-matrix>

== Non-Functional Requirements

#include "sections/nfr.typ"

#pagebreak()

== Test Plan

#include "sections/test-plan.typ"

#pagebreak(weak: true)