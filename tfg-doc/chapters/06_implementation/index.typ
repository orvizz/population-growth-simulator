// chapters/06_implementation/index.typ
#import "/template.typ": guia

= Implementation

== Application Structure

#guia[Describe here how your application is organised so that the reader understands
its different modules and deployed parts. This section is "free-form," and you should
consult with your tutor. Some guidelines to consider are:

- You can base this on the "Building Block View" and "Deployment View" sections of the
  ARC42 templates mentioned in the "Software Architecture" subject:
  #link("https://arc42.org/overview#building-block-view")[arc42.org/overview\#building-block-view]
- Please, do not repeat elements (this applies to the entire documentation). If you
  have already discussed something, simply reference the section where you did so
  (using cross-references). You can also insert links to external data sources.
- Do not copy and paste the entire code into this document; submit it as an attached
  file (unless there are specific parts that you must highlight for a particular
  reason).]

#guia[Package diagram / module tree]

// To show a code fragment:
// ```python
// def important_function():
//     ...
// ```

#pagebreak()

== CI/CD Pipeline Implementation

=== Repository Configuration

=== Branch Strategy and Protection Rules

=== Implemented Pipeline Stages

#guia[Screenshots of running pipeline]

=== Secret and Environment Variable Management

== Monitoring Implementation

=== Application Instrumentation

=== Prometheus Configuration

=== Grafana Dashboards

#guia[Screenshots of real dashboards]

=== Configured Alerts

#guia[If applicable]

== Implementation of Tests

#guia[Details of the tests designed according to the test plan will be included here.
For example, it may include scripts for manual test execution (if performed),
references to automatic execution scripts (e.g., pytest), as well as test execution
results that are of interest.

Note: It is highly recommended to include a summary table of the test results, showing
the percentage of passed/failed tests and code coverage if applicable.]
