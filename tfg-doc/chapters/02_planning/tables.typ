// chapters/02_planning/tables.typ
// All tables for the Planning & Management chapter
// Note: each table is wrapped in [...] so <labels> are in markup mode (not code mode)

// ── Stakeholders table ────────────────────────────────────────────────────────
#let stakeholders-table = [
  #figure(
    table(
      columns: (auto, 1fr, 1fr),
      stroke:  0.5pt,
      align:   (center + horizon, left + horizon, left + horizon),

      table.cell(colspan: 3, fill: black, align: center)[
        #text(fill: white, weight: "bold")[Stakeholders]
      ],
      table.cell(fill: luma(217))[*ID*],
      table.cell(fill: luma(217))[*Name*],
      table.cell(fill: luma(217))[*Description*],

      table.cell(colspan: 3, fill: rgb("DAE8FC"), align: center)[*Internal Stakeholders*],
      [SI-1], [Universidad de Oviedo],
        [University to whom the TFG belongs],
      [SI-2], [Biology Faculty of the University of Oviedo],
        [Faculty for whom the software is developed],
      [SI-3], [Software Engineering School of the University of Oviedo],
        [School to whom the student that will develop the software belongs],
      [SI-4], [Celia Melendi Lavandera],
        [TFG tutor belonging to the Software Engineering School],
      [SI-5], [Mario Quevedo de Anta],
        [TFG co-tutor belonging to the Biology Faculty],
      [SI-6], [Mario Orviz Viesca],
        [Student in charge of the planning, development, and documentation of this TFG],
      [SI-7], [Teachers and students from the Biology Faculty],
        [Actual real users for the application],

      table.cell(colspan: 3, fill: rgb("DAE8FC"), align: center)[*External Stakeholders*],
      [SE-1], [Max Planck Institute for Demographic Research (Germany)],
        [Institution that supports and hosts the COM(P)ADRE online repository for matrix
         population models (MPMs) and metadata],
      [SE-2], [Other biology organisms],
        [Some other biology organisms that might find this tool useful for their activity],
      [SE-3], [Hosting provider],
        [This product will be a web product, it will need a hosting provider],
    ),
    caption: [Internal and External Stakeholder identification],
  ) <tab:stakeholders>
]

// ── System users table ────────────────────────────────────────────────────────
#let system-users-table = [
  #figure(
    table(
      columns: (auto, 1fr, 1fr),
      stroke:  0.5pt,
      align:   (center + horizon, left + horizon, left + horizon),

      table.cell(colspan: 3, fill: black, align: center)[
        #text(fill: white, weight: "bold")[System Users]
      ],
      table.cell(fill: luma(217))[*ID*],
      table.cell(fill: luma(217))[*Name*],
      table.cell(fill: luma(217))[*Description*],

      [SU-1], [Non-registered user],
        [User that accesses the system without having an account or being logged in],
      [SU-2], [Registered user],
        [User that accesses the system being logged into their account],
    ),
    caption: [System Users],
  ) <tab:systemusers>
]

// ── OBS nodes table ───────────────────────────────────────────────────────────
#let obs-nodes-table = [
  #figure(
    table(
      columns: (auto, 1fr, 1fr),
      stroke:  0.5pt,
      align:   (center + horizon, left + horizon, left + horizon),

      table.cell(colspan: 3, fill: black, align: center)[
        #text(fill: white, weight: "bold")[OBS Nodes]
      ],
      table.cell(fill: luma(217))[*ID*],
      table.cell(fill: luma(217))[*Node*],
      table.cell(fill: luma(217))[*Description*],

      table.cell(colspan: 3, fill: rgb("DAE8FC"), align: center)[
        *1. Project Executor (SI-6)*
      ],
      [1.1], [Planning & Definition],
        [Scope definition, scheduling, stakeholder analysis, and risk planning.],
      [1.2], [Analysis & Design],
        [Requirements elicitation, system architecture, and interface design.],
      [1.3], [Development & Testing],
        [Implementation of all system components and verification activities.],
      [1.4], [Documentation & Closure],
        [TFG report writing, final delivery, and project closure tasks.],

      table.cell(colspan: 3, fill: rgb("DAE8FC"), align: center)[
        *2. Supervision & Acceptance Panel*
      ],
      [2.1], [SI-4 — Celia Melendi Lavandera],
        [Software Engineering tutor. Provides methodological guidance and reviews
         technical deliverables.],
      [2.2], [SI-5 — Mario Quevedo de Anta],
        [Biology co-tutor. Validates domain correctness and grants formal acceptance of
         the biological models implemented.],
    ),
    caption: [OBS node descriptions],
  ) <tab:obs>
]

// ── RACI table ────────────────────────────────────────────────────────────────
#let raci-blue = rgb(217, 217, 255)

#let raci-table = [
  #figure(
    table(
      columns: (1fr, auto, auto, auto),
      stroke:  0.5pt,
      align:   (left + horizon, center + horizon, center + horizon, center + horizon),

      table.cell(colspan: 4, fill: black, align: center)[
        #text(fill: white, weight: "bold")[Responsibility Assignment Matrix (RACI)]
      ],
      table.cell(fill: luma(217))[*Activity*],
      table.cell(fill: luma(217))[*SI-6 (Executor)*],
      table.cell(fill: luma(217))[*SI-4 (Tutor)*],
      table.cell(fill: luma(217))[*SI-5 (Co-tutor)*],

      [Planning & Definition],
        table.cell(fill: raci-blue)[R], [C], [I],
      [Requirements & Analysis],
        table.cell(fill: raci-blue)[R], [C], [A],
      [Architecture & Design],
        table.cell(fill: raci-blue)[R], [C], [I],
      [Development],
        table.cell(fill: raci-blue)[R], [I], [I],
      [Testing & Validation],
        table.cell(fill: raci-blue)[R], [C], [A],
      [TFG Documentation],
        table.cell(fill: raci-blue)[R], [A], [I],
      [Mid-project Review],
        table.cell(fill: raci-blue)[R], [C], [A],
      [Final Delivery & Closure],
        table.cell(fill: raci-blue)[R], [A], [C],
    ),
    caption: [RACI matrix — *R*: Responsible, *A*: Accountable/Accepts,
              *C*: Consulted, *I*: Informed],
  ) <tab:raci>
]
