// main.typ - document orchestrator
#import "template.typ": template, guia
#import "metadata.typ": *

// PDF metadata - must be set before any page is created
#set document(title: tfg-title, author: tfg-author, date: auto)

// ── Cover (no header / footer / page number) ──────────────────────────────────
#set page(
  paper:     "a4",
  margin:    (top: 25mm, bottom: 25mm, left: 30mm, right: 30mm),
  numbering: none,
  header:    none,
  footer:    none,
)
#include "cover.typ"
#pagebreak(weak: true)

// ── Apply template styles to all remaining content ────────────────────────────
#show: template

// ── Front matter (roman numerals, unnumbered headings) ────────────────────────
#set page(numbering: "i")
#counter(page).update(1)
#set heading(numbering: none)

// #include "chapters/00_disclaimer/index.typ"
// #pagebreak(weak: true)
#include "chapters/00_originality/index.typ"
#pagebreak(weak: true)
#include "chapters/00_acknowledgements/index.typ"

// ── Navigation indices ────────────────────────────────────────────────────────
#pagebreak(weak: true)
#outline(title: "Table of Contents", indent: auto, depth: 4)
#pagebreak(weak: true)
#outline(title: "List of Figures", target: figure.where(kind: image))
#pagebreak(weak: true)
#outline(
  title: "List of Tables",
  target: figure.where(kind: table)
    .or(figure.where(kind: "risk"))
    .or(figure.where(kind: "risk-contingency"))
    .or(figure.where(kind: "opportunity"))
    .or(figure.where(kind: "opportunity-action")),
)

// ── Main matter (arabic numerals, numbered headings) ──────────────────────────
#set page(numbering: "1")
#counter(page).update(1)
#set heading(numbering: "1.1")
#counter(heading).update(0) // reset so chapters start at 1

#include "chapters/01_description/index.typ"
#include "chapters/02_planning/index.typ"
#include "chapters/03_stakeholder_req/index.typ"
#include "chapters/04_system_req/index.typ"
#include "chapters/05_design/index.typ"
#include "chapters/06_implementation/index.typ"
#include "chapters/07_manuals/index.typ"
#include "chapters/08_conclusions/index.typ"
#include "chapters/09_appendix/index.typ"

// ── Bibliography ──────────────────────────────────────────────────────────────
#pagebreak()
#bibliography("sources.bib", style: "ieee", title: "Bibliography")
