#import "template.typ": project
#import "metadata.typ": *

#show: project.with(
  title: title,
  author: author,
  first_tutor: first_tutor,
  second_tutor: second_tutor,
)

// ── Contextual chapters ────────────────────────────────────────────────────
#include "chapters/introduction.typ"
#include "chapters/background.typ"
#include "chapters/scope.typ"

// ── Technical chapters ─────────────────────────────────────────────────────
#include "chapters/technology-stack.typ"
#include "chapters/architecture.typ"
#include "chapters/system-views.typ"
#include "chapters/api-design.typ"
#include "chapters/database.typ"
#include "chapters/simulation-engine.typ"
#include "chapters/testing.typ"
#include "chapters/devops.typ"
#include "chapters/cross-cutting-concepts.typ"


// ── Bibliography ───────────────────────────────────────────────────────────
#bibliography("refs.bib")
