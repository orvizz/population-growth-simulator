// chapters/04_system_req/index.typ
#import "/template.typ": guia, story-map

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

#guia[Insert your use case diagram here as a figure (rendered externally in PlantUML,
draw.io, etc. and saved as PNG/SVG under resources/).]

// Example — replace with your actual diagram:
// #figure(
//   image("/resources/diagrams/use-cases.png", width: 90%),
//   caption: [Use Case Diagram],
// ) <fig:use-cases>

==== Story Map

#figure(
  story-map((
    // Replace these epics and story titles to match your project.
    (epic: "Authentication", stories: ("Login", "Register", "Logout")),
    (epic: "Example Epic",   stories: ("Story A", "Story B")),
  )),
  caption: [User Story Map],
) <tab:story-map>

==== User Stories

// Each story lives in its own file under stories/.
// Add new stories there and register them in stories/_index.typ.
#include "stories/_index.typ"

=== Domain Data Model

#guia[Graphic representation with the different data entities the system interacts
with (e.g., using a class diagram).]

=== User Interface

#guia[Description of the requirements and conventions of the dialogue with the user,
including application navigation. If screen prototypes were created during the
project, they may also be included.]

#pagebreak()

== Non-Functional Requirements

#guia[Depending on the project, these will be organised into one or several sections
to include the rest of the requirements. Regarding non-functional requirements,
security requirements are frequent, following what was taught in the third-year subject
"Computer System Security".

In general, if security must be addressed transversally across the entire application,
it is recommended to follow the Level 1 requirements of the OWASP ASVS. If that is
not the case, and you want a minimum acceptable security level, consider the following:

- *Do not implement your own authentication system:* Always use an account system
  managed by a third party (Google, Microsoft...). This provides more security, saves
  development time, and improves usability.
- *Do not disable copy-paste* in password fields to allow the use of password managers.
- *Do not hardcode* passwords, API Keys, etc., in the code; use a vault or secret store.
- *SCA and SAST:* Ensure the code passes an SCA scan (to detect vulnerable dependencies)
  and a SAST scan (to avoid deploying code with security errors). GitHub provides these
  services easily.
- *WAF:* If it is a web application deployed publicly, do not go into production
  without a WAF (e.g., a free CloudFlare account).

If you do any of this, do not forget to document it properly and mention it in your
presentation.]

#pagebreak()

== Test Plan

#guia[At a minimum, the testing strategy must be specified, identifying the different
types and levels of testing, which part of the system they affect (test objects), as
well as the degree of automation and tools to be used in these activities.]

#guia[Explain the different layers of testing implemented:

- *Unit tests:* Unit testing per module or file.
- *Integration tests:* Describe the different integration tests. Specify the database
  used in each case, divide integration tests by section or module, and explain each
  integration test.
- *End-to-end tests:* Map end-to-end tests with the different user stories; these tests
  validate the solution of each individual user story.
- *Load tests:* Not just a set of users performing one action. Use Gatling to create
  statistics and performance reports, vary the tests (e.g., incrementing the load over
  time) to see at which point the application breaks. Map these tests to the
  non-functional performance requirements.
- *Usability tests:* Design usability tests for different user profiles (biology
  teachers, biology students, etc.). Prepare a questionnaire, measure times, and show
  the results in a graphical and intuitive way.]

#pagebreak(weak: true)