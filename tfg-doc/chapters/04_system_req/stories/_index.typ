// chapters/04_system_req/stories/_index.typ
// Include one file per user story, in narrative order.
// The user-story() counter is global: the first #include becomes US-01, the second US-02, etc.

// ── Authentication ────────────────────────────────────────────────────────────
#include "us-01-register.typ"
#include "us-02-login.typ"
#include "us-03-logout.typ"

// ── Browse Matrices ───────────────────────────────────────────────────────────
#include "us-04-browse-catalog.typ"
#include "us-05-search-filter.typ"
#include "us-06-view-detail.typ"
#include "us-07-export-matrix.typ"

// ── COMPADRE Integration ──────────────────────────────────────────────────────
#include "us-08-compadre-seed.typ"
#include "us-09-compadre-filter.typ"

// ── Custom Matrices ───────────────────────────────────────────────────────────
#include "us-10-create-matrix.typ"
#include "us-11-edit-matrix.typ"
#include "us-12-delete-matrix.typ"
#include "us-13-visibility.typ"
#include "us-14-share.typ"
#include "us-15-import-matrix.typ"

// ── Simulations ───────────────────────────────────────────────────────────────
#include "us-16-det-sim.typ"
#include "us-17-stoch-sim.typ"
#include "us-18-save-sim.typ"
#include "us-19-load-sim.typ"

// ── Ecological Analytics ──────────────────────────────────────────────────────
#include "us-20-analytics.typ"

// ── Quasi-Extinction ──────────────────────────────────────────────────────────
#include "us-21-qe-run.typ"
#include "us-22-qe-stages.typ"

// ── Testing & DevOps ──────────────────────────────────────────────────────────
#include "us-23-devops.typ"

// ── Internationalisation ──────────────────────────────────────────────────────
#include "us-24-language.typ"
