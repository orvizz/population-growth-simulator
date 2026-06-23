// chapters/02_planning/opportunities.typ
// Opportunity identification: one analysis card per identified opportunity,
// grouped by RBS category (the same Risk Breakdown Structure used for threats,
// see @sec:risk-mgmt-plan). Probability and per-objective impact levels follow
// the scales defined there; the merged score cell is Probability x
// best-affected-objective Impact, coloured by the zone it falls into on the
// Opportunity Probability-Impact Matrix (@tab:opp-pi-matrix).
#import "../../template.typ": opportunity-analysis, category-band

// ── Technical opportunities ─────────────────────────────────────────────────
#category-band[Technical Opportunities]

#opportunity-analysis(
  id: "OPP-T-01",
  name: [Reusable ecological-analytics library],
  category: [Technical, Quality],
  description: [The analytics service ($lambda_1$, stable stage distribution,
    reproductive value, sensitivities, elasticities) is already implemented as a
    self-contained module decoupled from FastAPI request/response concerns. If kept
    that way, it could be extracted into a standalone, pip-installable Python
    package for population ecology, useful to other students or researchers beyond
    this TFG.],
  probability: [Low (30%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Low (10%)],
    scope:    [Moderate (20%)],
    quality:  [High (40%)],
  ),
  score: [0.12], zone: "yellow",
  strategy: [Enhance],
  response: [Keep `api/services/analytics_service.py` free of FastAPI-specific
    types and database access so it can be extracted with minimal refactoring;
    keep `docs/analytics.md` as a self-contained mathematical reference suitable
    for an external package's documentation.],
  status: [Open, not pursued yet; the module is already structured to make
    this easy if revisited.],
)

#opportunity-analysis(
  id: "OPP-T-02",
  name: [COMPADRE ETL generalises to COMADRE faster than planned],
  category: [Technical, Technology],
  description: [COMADRE seeding is already identified as Future Work
    (@sec:future-work). If
    `db/seed_compadre.py`'s schema-driven parsing approach (`.RData` + `.parquet`
    to ORM rows) transfers cleanly to COMADRE's structure, that future-work item
    could be completed well ahead of schedule, with comparatively little
    additional engineering effort.],
  probability: [Medium (50%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Moderate (20%)],
    scope:    [Moderate (20%)],
    quality:  [Low (10%)],
  ),
  score: [0.10], zone: "yellow",
  strategy: [Exploit],
  response: [Keep the ETL pipeline's parsing logic schema-driven and well
    documented (column mapping, stage-name extraction) rather than hard-coded to
    COMPADRE specifics, so adapting it to COMADRE is a configuration change, not a
    rewrite.],
  status: [Open, not started; COMADRE remains a Future Work item
    (@sec:future-work).],
)

// ── External opportunities ──────────────────────────────────────────────────
#category-band[External Opportunities]

#opportunity-analysis(
  id: "OPP-E-01",
  name: [Institutional adoption interest from the Biology Faculty],
  category: [External, Market],
  description: [The Faculty of Biology stakeholders (#link(<stake:si-7>)[SI-7],
    and co-tutor #link(<stake:si-5>)[SI-5]) are actively engaged with the
    project. Positive reception during the TFG defense or earlier demos could
    turn "Institutional deployment" (currently a Future Work item,
    @sec:future-work) into a real, faculty-sponsored next step rather than a
    hypothetical one.],
  probability: [Medium (50%)],
  impact: (
    cost:     [Low (10%)],
    schedule: [Low (10%)],
    scope:    [High (40%)],
    quality:  [Moderate (20%)],
  ),
  score: [0.20], zone: "red",
  strategy: [Share],
  response: [Demonstrate the working platform to interested faculty and students
    during the TFG defense; keep the Installation and Operations manuals
    (@sec:installation-manual) detailed enough that a faculty-led rollout
    requires minimal extra documentation effort from the developer.],
  status: [Open, not yet raised with the Faculty beyond the existing
    collaboration.],
)

#opportunity-analysis(
  id: "OPP-E-02",
  name: [COMPADRE maintainers reference or link the tool],
  category: [External, Suppliers & Ext. Services],
  description: [The COMPADRE Plant Matrix Database team (Max Planck Institute for
    Demographic Research) maintains a public list of tools built on their data.
    If they became aware of this platform, a mention or link from them would
    meaningfully increase its visibility and credibility.],
  probability: [Low (30%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Very Low (5%)],
    scope:    [Low (10%)],
    quality:  [Moderate (20%)],
  ),
  score: [0.06], zone: "yellow",
  strategy: [Accept],
  response: [No active outreach planned within the TFG's scope; the COMPADRE
    database is already credited prominently in the bibliography and in the
    Browse Matrices tab's source attribution, so the project is already well
    positioned if contacted.],
  status: [Open, not pursued.],
)

// ── Organizational opportunities ────────────────────────────────────────────
#category-band[Organizational Opportunities]

#opportunity-analysis(
  id: "OPP-O-01",
  name: [Unused buffer days reinvested in extra features],
  category: [Organizational, Resources],
  description: [The 14-day documentation schedule (`schedule.md`) reserves two
    buffer days for review and polish. If the threats that could consume them
    (@tab:risk-o-02, @tab:risk-pm-01) do not materialise, that time becomes
    available to pull forward Should/Could-priority items instead of just
    reviewing.],
  probability: [Medium (50%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Low (10%)],
    scope:    [Moderate (20%)],
    quality:  [Low (10%)],
  ),
  score: [0.10], zone: "yellow",
  strategy: [Exploit],
  response: [Keep the MoSCoW-prioritised backlog (@sec:stories) ranked and
    ready, so the next Should/Could item can be pulled in immediately if a
    phase finishes under its planned duration, instead of leaving the time
    unallocated.],
  status: [Open, contingent on @tab:risk-o-02/@tab:risk-pm-01 not materialising.],
)

// ── Project Management opportunities ────────────────────────────────────────
#category-band[Project Management Opportunities]

#opportunity-analysis(
  id: "OPP-PM-01",
  name: [Tutor check-ins surface co-authorship / domain insight],
  category: [Project Management, Communication],
  description: [The bi-weekly tutor check-ins set up to mitigate the
    feedback-delay risk (@tab:risk-pm-03) are a standing two-way channel, not just a
    status report. Domain insight volunteered by the biology co-tutor during
    these sessions could exceed simple validation and point toward a joint
    publication or a more rigorous ecological analysis than originally scoped.],
  probability: [Low (30%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Very Low (5%)],
    scope:    [Low (10%)],
    quality:  [High (40%)],
  ),
  score: [0.12], zone: "yellow",
  strategy: [Enhance],
  response: [Treat the check-ins as a two-way conversation rather than a
    one-way status update; explicitly invite and record any domain observations
    from the co-tutor, even ones outside the immediate requirements, for
    possible follow-up after the TFG.],
  status: [Open, ongoing via the existing bi-weekly check-ins.],
)
