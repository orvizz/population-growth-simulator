// chapters/09_appendix/risk_management_plan.typ
#import "../../template.typ": obs-node, risk-contingency, opportunity-action
#import "tables.typ": probability-scale-table, impact-scale-table, probability-impact-matrix-table, opportunity-probability-impact-matrix-table

Risk management on this project follows a Probability-Impact methodology adapted from
the PMBOK Guide for a single-developer academic project, covering both *threats*
(negative risks) and *opportunities* (positive risks) with the same machinery. It has
four steps: (1) classify candidate risks using a Risk Breakdown Structure (RBS), (2)
rate each one's probability and impact against fixed qualitative scales, (3) compute an
exposure score and place it on a Probability-Impact Matrix to prioritise it, and (4)
define a contingency plan for every threat -- or an exploitation plan for every
opportunity -- that lands in the matrix's red zone. The resulting risk identification
and Risk Register live in @sec:risks, and the opportunity identification and
Opportunity Register live in @sec:opportunities, both in the planning chapter.

=== Risk Breakdown Structure

Risks and opportunities are grouped into the same four top-level categories, each split
into subcategories that narrow down the likely source of the risk. Not every
subcategory has a risk or opportunity assigned to it yet; the RBS is the fixed
classification scheme used throughout the project, not a list of risks itself.

#figure(
  {
    set text(size: 9pt)

    align(center,
      block(width: 50%,
        obs-node(fill: rgb(50, 50, 50))[
          #text(fill: white, weight: "bold", size: 11pt)[Project Risks]
        ]
      )
    )

    v(8pt)

    grid(
      columns: (1fr, 1fr, 1fr, 1fr),
      gutter:  10pt,

      {
        obs-node(fill: rgb(188, 210, 238))[*Technical*]
        v(4pt)
        for sub in ("Requirements", "Technology", "Complexity & Interfaces",
                    "Performance & Reliability", "Quality", "Security") {
          obs-node(fill: rgb(219, 229, 241))[#sub]
          v(3pt)
        }
      },
      {
        obs-node(fill: rgb(219, 238, 188))[*External*]
        v(4pt)
        for sub in ("Suppliers & Ext. Services", "Regulation", "Market", "Users",
                    "Schedule Dependencies") {
          obs-node(fill: rgb(229, 241, 219))[#sub]
          v(3pt)
        }
      },
      {
        obs-node(fill: rgb(238, 219, 188))[*Organizational*]
        v(4pt)
        for sub in ("Project Dependencies", "Resources", "Financing", "Prioritization") {
          obs-node(fill: rgb(241, 229, 219))[#sub]
          v(3pt)
        }
      },
      {
        obs-node(fill: rgb(230, 188, 238))[*Project Management*]
        v(4pt)
        for sub in ("Estimation", "Planning", "Control", "Communication") {
          obs-node(fill: rgb(237, 219, 241))[#sub]
          v(3pt)
        }
      },
    )
  },
  caption: [Risk Breakdown Structure (RBS).],
) <fig:rbs>

=== Probability and Impact Scales

Probability is rated on a five-level qualitative scale (@tab:probability-scale). Impact
is rated independently against four project objectives -- cost, schedule, scope, and
quality -- using the scale in @tab:impact-scale, so that a risk threatening, say, the
scientific validity of the simulation results (quality) is not understated just because
it has no cost or schedule effect.

#probability-scale-table

#impact-scale-table

@tab:impact-scale describes negative consequences, for rating threats. The same
numeric thresholds apply to opportunities, but represent a *positive* contribution to
the equivalent objective instead -- e.g. a schedule reduction rather than a schedule
increase, or a quality improvement rather than a quality degradation.

=== Probability-Impact Matrix

For each risk, the exposure score is *probability x impact*, where impact is the
*highest-rated objective* for that risk (its worst-case dimension). @tab:pi-matrix maps
every probability/impact combination to a priority zone: green risks are accepted and
simply monitored, yellow risks are actively mitigated, and red risks additionally
require a documented contingency plan, provided below for every red-zone risk
identified in @sec:risk-mgmt-plan.

#probability-impact-matrix-table

=== Opportunity Probability-Impact Matrix

Opportunities are scored the same way (*probability x impact*, using the
best-rated objective) and placed on the same matrix shape (@tab:opp-pi-matrix).
The zones carry the opposite meaning: red is the highest priority to actively
*exploit*, not the highest priority to mitigate. Green opportunities are accepted and
simply monitored; yellow opportunities are actively enhanced; red opportunities get a
dedicated exploitation plan, provided below.

#opportunity-probability-impact-matrix-table

=== Contingency Plans

Five identified risks fall in the matrix's red zone: @tab:risk-t-01 (simulation and
analytics correctness errors), @tab:risk-o-01 (sole-developer key-person risk),
@tab:risk-o-02 (competing coursework workload), @tab:risk-pm-01 (effort estimation /
schedule slippage), and @tab:risk-pm-02 (scope creep from stakeholder requests). Each
has a contingency plan below, to be activated if the trigger condition occurs.

#risk-contingency(
  id: "T-01",
  name: [Simulation and analytics correctness errors],
  trigger: [A unit test or a co-tutor review reveals that computed analytics
    ($lambda_1$, sensitivities, elasticities) or simulation output disagrees with a
    known reference case from Caswell (2001) or with the co-tutor's manual
    calculation.],
  owner: [Sole developer (Mario Orviz Viesca), with biological validation from the
    co-tutor (#link(<stake:si-5>)[SI-5], Mario Quevedo de Anta).],
  immediate: [Freeze the affected endpoint behind the test suite. Do not present the
    corresponding result as validated in this document until corrected; write a unit
    test that reproduces the discrepancy.],
  short-term: [Re-derive the formula to correct the discrepancy; add a
    regression test pinned to the corrected reference values; request a follow-up
    review from the co-tutor.],
  reserve: [Use up to one documentation buffer day to
    re-verify and re-write the affected analytics section.],
)

#risk-contingency(
  id: "O-01",
  name: [Sole-developer key-person risk],
  trigger: [The developer is unavailable (illness, personal emergency) for more than
    three consecutive working days during an active phase.],
  owner: [Sole developer; both tutors are informed as soon as the absence is
    identified.],
  immediate: [Notify both tutors of the interruption and the expected return date;
    commit and push all work-in-progress so no work is at risk of loss.],
  short-term: [Re-baseline the schedule on return, consuming available buffer days
    first; if the absence exceeds one week, descope Should/Could-priority user stories
    (MoSCoW priorities, @sec:stories) to protect the Must-priority core.],
  reserve: [Consume the schedule's buffer days (Day 13-14) and, if exhausted, request a
    submission deadline extension through the academic tutor.],
)

#risk-contingency(
  id: "O-02",
  name: [Competing coursework workload],
  trigger: [Weekly tracking shows actual progress more than three days behind the
    planned schedule for two consecutive weeks.],
  owner: [Sole developer.],
  immediate: [Re-prioritise the current week using MoSCoW priorities; pause
    Could/Should items in favour of Must items.],
  short-term: [Reallocate planned buffer days (Day 13-14) to the affected chapter; if
    slippage persists, move Should-priority future-work items (@sec:future-work) out
    of the current scope.],
  reserve: [Up to two buffer days reallocated from the documentation review phase.],
)

#risk-contingency(
  id: "PM-01",
  name: [Effort estimation / schedule slippage],
  trigger: [A phase's actual duration exceeds its planned duration by more than 50%
    (per the Tracking Plan, @sec:tracking-plan).],
  owner: [Sole developer.],
  immediate: [Log the deviation in the Project Issue Log with its cause and the
    estimated extra effort required.],
  short-term: [Re-estimate the remaining phases using the observed velocity rather
    than the original plan; trim Should/Could-priority scope first.],
  reserve: [Use the schedule's built-in buffer days before requesting any deadline
    extension.],
)

#risk-contingency(
  id: "PM-02",
  name: [Scope creep from stakeholder requests],
  trigger: [A stakeholder (Biology Faculty) formally requests a feature not present in
    the SR-F baseline (@sec:stakeholder-requirements).],
  owner: [Sole developer, with acceptance authority resting with the academic tutor
    (#link(<stake:si-4>)[SI-4] is Accountable for requirements decisions per the
    RACI matrix, @tab:raci).],
  immediate: [Log the request in the Project Issue Log; do not implement it without
    baseline approval.],
  short-term: [Evaluate the request against current Must-priority backlog capacity; if
    accepted, add it to Future Work (@sec:future-work) rather than the current
    release, unless a Must-priority item is descoped to compensate.],
  reserve: [None by design -- scope changes do not consume schedule reserve; they are
    deferred instead.],
)

=== Opportunity Exploitation Plans

One identified opportunity falls in the matrix's red zone: @tab:opportunity-opp-e-01
(institutional adoption interest from the Biology Faculty). It has an exploitation
plan below, to be activated if the opportunity arises.

#opportunity-action(
  id: "OPP-E-01",
  name: [Institutional adoption interest from the Biology Faculty],
  trigger: [A Faculty of Biology stakeholder (#link(<stake:si-7>)[SI-7]) or the
    co-tutor (#link(<stake:si-5>)[SI-5]) expresses interest, during a demo or the
    TFG defense, in using the platform beyond the scope of this TFG.],
  owner: [Sole developer, with the academic tutor (#link(<stake:si-4>)[SI-4]) and
    co-tutor (#link(<stake:si-5>)[SI-5]) as the natural points of contact for any
    institutional follow-up.],
  immediate: [Acknowledge the interest and note it in the Project Issue Log; avoid
    making delivery commitments beyond what the Installation and Operations manuals
    (@sec:installation-manual) already support.],
  short-term: [Walk the interested party through the Installation manual
    (@sec:installation-manual) for a self-hosted deployment, or scope a minimal
    institutional deployment (per the Future Work item, @sec:future-work) as a
    separate, explicitly out-of-TFG-scope effort.],
  resourcing: [No additional resourcing within the TFG's timeline; any real
    deployment work is treated as Future Work (@sec:future-work), pursued after
    submission.],
)
