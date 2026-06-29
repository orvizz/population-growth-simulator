// chapters/09_appendix/index.typ
#import "../../template.typ": guia
#import "tables.typ": delivery-table, repo-structure-table

= Appendices

== Risk Management Plan <sec:risk-mgmt-plan>

#include "risk_management_plan.typ"

// == Bibliographic References

// #guia[Please do not confuse a reference list with a general bibliography.

// - *References:* Includes only sources directly cited in your text. Use `@key` in
//   Typst to cite. This provides the necessary information for the reader to locate the
//   specific sources used to support your arguments.
// - *General Bibliography:* A broader list of sources consulted or relevant to your
//   research, whether cited or not. All sources that appear in `sources.bib` and are
//   cited in the text will appear in the bibliography section.

// The reference to this template must be kept as follows:]



// / [1]: J. M. Redondo, "Documentos-modelo para Trabajos de Fin de Grado/Master de la
//   Escuela de Ingeniería Informática de Oviedo," 17 6 2019. \[Online\]. Available:
//   #link("https://www.researchgate.net/publication/327882831_Plantilla_de_Proyectos_de_Fin_de_Carrera_de_la_Escuela_de_Informatica_de_Oviedo")

// #pagebreak()

== Content Delivered <sec:delivered-content>

The physical submission consists of the two files listed in @tab:delivery.
Because the project artefacts (source code, database seed data, Docker
configuration, and CI pipelines) are hosted in a public GitHub repository,
no source archive is bundled with the PDF. The `README.txt` file contains
the two URLs needed to access the live application and to inspect or clone
the full project.

#delivery-table

=== Repository Structure

The public repository at
#link("https://github.com/orvizz/population-growth-simulator") is organised
as a monorepo containing the backend API, the frontend web application, the
database layer, automated tests, and the CI/CD workflow definitions.
@tab:repo-structure describes the top-level directories and key files.

#repo-structure-table
