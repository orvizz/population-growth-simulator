// chapters/05_design/index.typ
#import "/template.typ": guia

= Design

== Architectural Design

#guia[Clearly describe the architectural concepts and the frameworks used, as well as
their interaction with the environment and other systems. Usually, this begins with an
initial block diagram showing the different components, systems, and their
relationships.

It is important to add Deployment Diagrams documenting in which nodes each component
has been deployed. The use of UML diagrams is recommended, and remember that each
diagram must have an extensive explanatory text describing the objective and operation
of the elements contained in said diagram.]

=== High-Level Overview

#guia[Block and component diagrams]

=== Service Architecture

#guia[UML compound diagrams]

=== Deployment and Infrastructure

#guia[UML deployment diagram]

== Detailed Design

#guia[In the detailed design, it is more important to describe the concepts of how the
application works, accompanied by a selection of graphic representations (e.g., UML),
rather than including many graphics with minor details. It will also include the
description of the code structure that forms part of the application in relation to the
components defined in the architecture.

If design patterns have been used, each of them must be documented according to the
following scheme:
- Name of the pattern.
- For each instantiation: relation of pattern roles and the class associated with
  each one.]

=== Main System Flows

#guia[UML sequence diagrams]

=== Persistent Data Model

#guia[Detailed ER or class diagram]

=== Design Patterns Applied

== Development Workflow and Tooling

=== Repository and Version Control

#guia[Branch model diagram (GitFlow or equivalent)]

=== Team Workflow

#guia[Lifecycle flow diagram: issue → branch → PR → review → merge]

== Continuous Integration and Deployment (CI/CD)

=== Pipeline Overview

#guia[CI/CD pipeline flow diagram]

=== Continuous Integration

#guia[CI stage activity diagram]

=== Continuous Deployment

#guia[CD stage activity diagram]

== Monitoring Design

=== Observability Strategy

=== Monitoring Architecture

#guia[Component diagram: app → exporters → Prometheus → Grafana]

=== Dashboard and Alert Design

#guia[Grafana dashboard mockups]

== Test Design

#guia[This section is closely related to section 4.3. The test plan (section 4.3)
describes _what_ will be tested; this section describes _how_ it will be designed.
Section 6.4 will then show the actual implementation and results.]
