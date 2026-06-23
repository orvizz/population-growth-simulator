// template.typ - all styles, layout rules, and reusable component functions
#import "metadata.typ": tfg-title, tfg-author

// ── Colours ───────────────────────────────────────────────────────────────────
#let uniovi-blue = rgb(0, 172, 233)
#let guia-color  = rgb(139, 69, 19)

// ── Utility functions ─────────────────────────────────────────────────────────

// Brown italic placeholder text - must be removed in the final version
#let guia(content) = text(fill: guia-color, style: "italic")[#content]

// ── Requirement counter and prefix state ─────────────────────────────────────
#let _req-c      = counter("req")
#let _req-prefix = state("req-prefix", "SR")

// Call before each requirement block to set the prefix (e.g. "SR-F", "SR-NF")
// and reset the counter so numbering starts from 01.
#let req-group(prefix) = {
  _req-prefix.update(prefix)
  _req-c.update((0, 0, 0, 0, 0, 0))
}

// Auto-numbered requirement item.
//   indent 0 → top level:  SR-F-01
//   indent 1 → sub-req:    SR-F-01.1
//   indent 2 → leaf:       SR-F-01.1.1  (up to 6 levels)
// Each item gets a label <req:sr-f-01.1.1> for cross-referencing via @req:...
#let req(title, content, indent: 0) = {
  _req-c.step(level: indent + 1)
  context {
    let pfx  = _req-prefix.get()
    let nums = _req-c.get()
    let p2(n) = if n < 10 { "0" + str(n) } else { str(n) }

    let id = pfx + "-" + p2(nums.at(0, default: 1)) + range(1, indent + 1).fold("", (acc, i) => acc + "." + str(nums.at(i, default: 1)))

    let accents = (
      uniovi-blue,
      uniovi-blue.lighten(20%),
      uniovi-blue.lighten(38%),
      uniovi-blue.lighten(52%),
      uniovi-blue.lighten(63%),
      uniovi-blue.lighten(72%),
    )
    let widths = (4pt, 3pt, 2.5pt, 2pt, 1.5pt, 1pt)
    let lvl    = calc.min(indent, accents.len() - 1)

    let item = pad(
      left: indent * 1.1em,
      block(
        width:  100%,
        above:  if indent == 0 { 1.2em } else { 0.45em },
        below:  0.25em,
        stroke: (left: widths.at(lvl) + accents.at(lvl)),
        inset:  (left: 0.55em, top: 0.25em, bottom: 0.25em, right: 0pt),
      )[*#id.* *#title:* #content],
    )

    [#figure(
      align(left, item),
      kind:       "req",
      supplement: [#id],
      numbering:  none,
      caption:    none,
      outlined:   false,
    )#label("req:" + lower(id))]
  }
}

// ── User-story counter and card ───────────────────────────────────────────────
#let _us-c = counter("user-story")

#let user-story(
  role:     [],
  want:     [],
  benefit:  [],
  priority: "Must",
  points:   [],
  criteria: (),
) = {
  _us-c.step()
  context {
    let n  = _us-c.get().at(0)
    let p2 = n => if n < 10 { "0" + str(n) } else { str(n) }
    let id = "US-" + p2(n)

    let priority-color = if priority == "Must"   { rgb(255, 200, 200) }
      else if priority == "Should" { rgb(255, 230, 180) }
      else if priority == "Could"  { rgb(200, 235, 200) }
      else                          { luma(220) }

    let card = block(
      width:  100%,
      stroke: 0.5pt + luma(180),
      radius: 4pt,
      clip:   true,
      below:  1em,
    )[
      #block(
        width: 100%,
        fill:  uniovi-blue.lighten(80%),
        inset: (x: 10pt, y: 6pt),
      )[
        #grid(
          columns: (1fr, auto, auto),
          align:   (left + horizon, right + horizon, right + horizon),
          gutter:  8pt,
          [*#id*],
          box(fill: priority-color, radius: 3pt, inset: (x: 6pt, y: 3pt))[
            #text(size: 9pt, weight: "bold")[#priority]
          ],
          box(fill: luma(230), radius: 3pt, inset: (x: 6pt, y: 3pt))[
            #text(size: 9pt)[#points pt]
          ],
        )
      ]
      #block(inset: (x: 10pt, y: 8pt), width: 100%)[
        #emph[As a *#role*, I want to *#want*, so that *#benefit*.]
        #if criteria.len() > 0 {
          v(6pt)
          line(length: 100%, stroke: 0.5pt + luma(200))
          v(4pt)
          text(size: 10pt, weight: "bold")[Acceptance Criteria]
          v(4pt)
          for c in criteria {
            [• #c \ ]
          }
        }
      ]
    ]

    [#figure(
      card,
      kind:       "user-story",
      supplement: [#id],
      numbering:  none,
      caption:    none,
      outlined:   false,
    )#label("us:" + p2(n))]
  }
}

// ── Use-case counter and table ────────────────────────────────────────────────
#let _uc-c = counter("use-case")

#let use-case(
  name:           [],
  description:    [],
  actors:         [],
  trigger:        [],
  preconditions:  [],
  postconditions: [],
  normal-flow:    (),
  alt-flows:      none,
  exceptions:     none,
) = {
  _uc-c.step()
  context {
    let n  = _uc-c.get().at(0)
    let p2 = n => if n < 10 { "0" + str(n) } else { str(n) }
    let id = "UC-" + p2(n)

    let label-fill   = luma(240)
    let border-color = luma(180)

    let flow-content = {
      for (i, step) in normal-flow.enumerate() {
        [#(i + 1). #step \ ]
      }
    }

    let rows = (
      ([*Description*],    description),
      ([*Actors*],         actors),
      ([*Trigger*],        trigger),
      ([*Preconditions*],  preconditions),
      ([*Postconditions*], postconditions),
      ([*Normal flow*],    flow-content),
    ) + (if alt-flows  != none { (([*Alternative flows*], alt-flows ),) } else { () }) + (if exceptions != none { (([*Exceptions*],        exceptions),) } else { () })

    let tbl = block(
      width:  100%,
      stroke: 0.5pt + border-color,
      radius: 3pt,
      clip:   true,
      below:  1em,
    )[
      #block(
        width: 100%,
        fill:  uniovi-blue,
        inset: (x: 10pt, y: 7pt),
      )[
        #text(fill: white, weight: "bold")[#id - #name]
      ]
      #table(
        columns:  (32%, 1fr),
        stroke:   0.5pt + border-color,
        fill: (col, _) => if col == 0 { label-fill } else { white },
        inset:    (x: 8pt, y: 5pt),
        ..rows.map(r => (r.at(0), r.at(1))).flatten(),
      )
    ]

    [#figure(
      align(left, tbl),
      kind:       "use-case",
      supplement: [#id],
      numbering:  none,
      caption:    none,
      outlined:   false,
    )#label("uc:" + p2(n))]
  }
}

// ── Scenario counter and table ────────────────────────────────────────────────
#let _sc-c = counter("scenario")

#let scenario(
  name:           [],
  description:    [],
  actors:         [],
  trigger:        [],
  preconditions:  [],
  postconditions: [],
  sequence:       (),
) = {
  _sc-c.step()
  context {
    let n  = _sc-c.get().at(0)
    let p2 = n => if n < 10 { "0" + str(n) } else { str(n) }
    let id = "SC-" + p2(n)

    let label-fill   = luma(240)
    let header-fill  = uniovi-blue.lighten(15%)
    let border-color = luma(180)

    let seq-content = {
      for (i, step) in sequence.enumerate() {
        [#(i + 1). #step \ ]
      }
    }

    let rows = (
      ([*Description*],    description),
      ([*Actors*],         actors),
      ([*Trigger*],        trigger),
      ([*Preconditions*],  preconditions),
      ([*Postconditions*], postconditions),
      ([*Sequence*],       seq-content),
    )

    let tbl = block(
      width:  100%,
      stroke: 0.5pt + border-color,
      radius: 3pt,
      clip:   true,
      below:  1em,
    )[
      #block(
        width: 100%,
        fill:  header-fill,
        inset: (x: 10pt, y: 7pt),
      )[
        #text(fill: white, weight: "bold")[#id - #name]
      ]
      #table(
        columns:  (32%, 1fr),
        stroke:   0.5pt + border-color,
        fill: (col, _) => if col == 0 { label-fill } else { white },
        inset:    (x: 8pt, y: 5pt),
        ..rows.map(r => (r.at(0), r.at(1))).flatten(),
      )
    ]

    [#figure(
      align(left, tbl),
      kind:       "scenario",
      supplement: [#id],
      numbering:  none,
      caption:    none,
      outlined:   false,
    )#label("sc:" + p2(n))]
  }
}

// Renders a story-map grid grouped by epic.
// epics: array of (epic: str, stories: array of str)
// Wrap in #figure(...) <tab:story-map> at the call site.
#let story-map(epics) = {
  let col-count   = epics.len()
  let max-stories = epics.fold(0, (acc, e) => calc.max(acc, e.stories.len()))

  let header-cells = epics.map(e =>
    table.cell(fill: uniovi-blue, align: center)[
      #text(fill: white, weight: "bold")[#e.epic]
    ]
  )

  let body-rows = range(max-stories).map(row =>
    epics.map(e =>
      if row < e.stories.len() { [#e.stories.at(row)] }
      else                      { [] }
    )
  ).flatten()

  table(
    columns: range(col-count).map(_ => 1fr),
    ..header-cells,
    ..body-rows,
  )
}

// ── Risk analysis card ────────────────────────────────────────────────────────
// Renders one identified risk as a labelled card: description, category,
// probability, per-objective impact (with a merged exposure-score cell coloured
// by P-I matrix zone), response strategy, planned response, and current status.
#let risk-zone-color(zone) = if zone == "red" { rgb("EF9A9A") }  else if zone == "yellow" { rgb("FFD54F") }else { rgb("81C784") }

// Shared band used to separate RBS categories in risks.typ / opportunities.typ
#let category-band(title) = block(
  width:  100%,
  fill:   rgb("DAE8FC"),
  inset:  (x: 8pt, y: 6pt),
  above:  1.2em,
  below:  0.6em,
)[*#title*]

#let risk-analysis(
  id:          "",
  name:        [],
  category:    [],
  description: [],
  probability: "",
  impact:      (cost: "", schedule: "", scope: "", quality: ""),
  score:       0.0,
  zone:        "green",
  strategy:    "",
  response:    [],
  status:      "Open",
) = {
  let label-fill   = luma(240)
  let border-color = luma(180)

  let card = block(
    width:  100%,
    stroke: 0.5pt + border-color,
    radius: 3pt,
    clip:   true,
    below:  1em,
  )[
    #block(width: 100%, fill: uniovi-blue, inset: (x: 10pt, y: 7pt))[
      #text(fill: white, weight: "bold")[#id --- #name]
    ]
    #table(
      columns: (22%, 26%, 1fr, 13%),
      stroke:  0.5pt + border-color,
      fill:    (col, _) => if col == 0 { label-fill } else { white },
      inset:   (x: 8pt, y: 5pt),
      align:   (left + horizon, left + horizon, left + horizon, center + horizon),

      [*Description*], table.cell(colspan: 3)[#description],
      [*Category*],    table.cell(colspan: 3)[#category],
      [*Probability*], table.cell(colspan: 3)[#probability],

      table.cell(rowspan: 4)[*Impact*],
        [Cost],     [#impact.cost],
        table.cell(rowspan: 4, fill: risk-zone-color(zone), align: center + horizon)[
          #text(weight: "bold")[#score]
        ],
        [Schedule], [#impact.schedule],
        [Scope],    [#impact.scope],
        [Quality],  [#impact.quality],

      [*Strategy*], table.cell(colspan: 3)[#strategy],
      [*Response*], table.cell(colspan: 3)[#response],
      [*Status*],   table.cell(colspan: 3)[#status],
    )
  ]

  [#figure(
    align(left, card),
    kind:       "risk",
    supplement: [#id],
    numbering:  none,
    caption:    none,
    outlined:   false,
  )#label("tab:risk-" + lower(id))]
}

// ── Risk contingency plan card ───────────────────────────────────────────────
// For red-zone risks only: trigger condition, owner, immediate / short-term
// actions, and how the schedule reserve is consumed if the risk materialises.
#let risk-contingency(
  id:            "",
  name:          [],
  trigger:       [],
  owner:         [],
  immediate:     [],
  short-term:    [],
  reserve:       [],
) = {
  let label-fill   = luma(240)
  let border-color = luma(180)

  let card = block(
    width:  100%,
    stroke: 0.5pt + border-color,
    radius: 3pt,
    clip:   true,
    below:  1em,
  )[
    #block(width: 100%, fill: luma(60), inset: (x: 10pt, y: 7pt))[
      #text(fill: white, weight: "bold")[Contingency Plan - #id - #name]
    ]
    #table(
      columns:  (26%, 1fr),
      stroke:   0.5pt + border-color,
      fill:     (col, _) => if col == 0 { label-fill } else { white },
      inset:    (x: 8pt, y: 5pt),
      align:    (left + horizon, left + horizon),

      [*Trigger*],            [#trigger],
      [*Owner*],               [#owner],
      [*Immediate actions*],   [#immediate],
      [*Short-term actions*],  [#short-term],
      [*Reserve usage*],       [#reserve],
    )
  ]

  [#figure(
    align(left, card),
    kind:       "risk-contingency",
    supplement: [#id],
    numbering:  none,
    caption:    none,
    outlined:   false,
  )#label("tab:contingency-" + lower(id))]
}

// ── Opportunity analysis card ───────────────────────────────────────────────
// Mirrors risk-analysis() for positive risks: same shape, but strategy uses the
// PMBOK opportunity terms (Exploit / Enhance / Share / Accept) and a distinct
// (green) header color so opportunity cards read differently from threat cards.
#let opportunity-analysis(
  id:          "",
  name:        [],
  category:    [],
  description: [],
  probability: "",
  impact:      (cost: "", schedule: "", scope: "", quality: ""),
  score:       0.0,
  zone:        "green",
  strategy:    "",
  response:    [],
  status:      "Open",
) = {
  let label-fill   = luma(240)
  let border-color = luma(180)
  let header-color = rgb(46, 139, 87)

  let card = block(
    width:  100%,
    stroke: 0.5pt + border-color,
    radius: 3pt,
    clip:   true,
    below:  1em,
  )[
    #block(width: 100%, fill: header-color, inset: (x: 10pt, y: 7pt))[
      #text(fill: white, weight: "bold")[#id --- #name]
    ]
    #table(
      columns: (22%, 26%, 1fr, 13%),
      stroke:  0.5pt + border-color,
      fill:    (col, _) => if col == 0 { label-fill } else { white },
      inset:   (x: 8pt, y: 5pt),
      align:   (left + horizon, left + horizon, left + horizon, center + horizon),

      [*Description*], table.cell(colspan: 3)[#description],
      [*Category*],    table.cell(colspan: 3)[#category],
      [*Probability*], table.cell(colspan: 3)[#probability],

      table.cell(rowspan: 4)[*Impact*],
        [Cost],     [#impact.cost],
        table.cell(rowspan: 4, fill: risk-zone-color(zone), align: center + horizon)[
          #text(weight: "bold")[#score]
        ],
        [Schedule], [#impact.schedule],
        [Scope],    [#impact.scope],
        [Quality],  [#impact.quality],

      [*Strategy*], table.cell(colspan: 3)[#strategy],
      [*Response*], table.cell(colspan: 3)[#response],
      [*Status*],   table.cell(colspan: 3)[#status],
    )
  ]

  [#figure(
    align(left, card),
    kind:       "opportunity",
    supplement: [#id],
    numbering:  none,
    caption:    none,
    outlined:   false,
  )#label("tab:opportunity-" + lower(id))]
}

// ── Opportunity action plan card ────────────────────────────────────────────
// For red-zone opportunities only: mirrors risk-contingency(), but the last
// field is "resourcing" (what it takes to pursue it) rather than "reserve
// usage" (which only makes sense for reacting to a threat).
#let opportunity-action(
  id:            "",
  name:          [],
  trigger:       [],
  owner:         [],
  immediate:     [],
  short-term:    [],
  resourcing:    [],
) = {
  let label-fill   = luma(240)
  let border-color = luma(180)

  let card = block(
    width:  100%,
    stroke: 0.5pt + border-color,
    radius: 3pt,
    clip:   true,
    below:  1em,
  )[
    #block(width: 100%, fill: rgb(30, 90, 80), inset: (x: 10pt, y: 7pt))[
      #text(fill: white, weight: "bold")[Exploitation Plan - #id - #name]
    ]
    #table(
      columns:  (26%, 1fr),
      stroke:   0.5pt + border-color,
      fill:     (col, _) => if col == 0 { label-fill } else { white },
      inset:    (x: 8pt, y: 5pt),
      align:    (left + horizon, left + horizon),

      [*Trigger*],            [#trigger],
      [*Owner*],               [#owner],
      [*Immediate actions*],   [#immediate],
      [*Short-term actions*],  [#short-term],
      [*Resourcing*],          [#resourcing],
    )
  ]

  [#figure(
    align(left, card),
    kind:       "opportunity-action",
    supplement: [#id],
    numbering:  none,
    caption:    none,
    outlined:   false,
  )#label("tab:oppty-action-" + lower(id))]
}

// Box used in the OBS tree diagram
#let obs-node(fill: white, content) = block(
  fill:   fill,
  stroke: 0.5pt + luma(160),
  radius: 3pt,
  inset:  (x: 8pt, y: 6pt),
  width:  100%,
  align(center, content),
)

// ── Template function ─────────────────────────────────────────────────────────
#let template(body) = {
  // Page geometry, header, footer
  set page(
    paper:  "a4",
    margin: (top: 25mm, bottom: 25mm, left: 30mm, right: 30mm),
    header: align(center, image("resources/logos/eii_header.png", height: 2cm, width: auto)),
    header-ascent: 5mm,
    footer: context {
      set text(size: 9pt)
      grid(
        columns: (1fr, auto),
        align:   (left + horizon, right + horizon),
        [#smallcaps(emph[#tfg-title]) \ #tfg-author],
        counter(page).display(),
      )
    },
    footer-descent: 12mm,
  )

  // Base text and paragraph settings
  set text(font: "Roboto", size: 11pt)
  set par(
    justify:           true,
    first-line-indent: 0pt,
    spacing:           1em,
    leading:           0.8em,
  )

  // ── Heading styles ──────────────────────────────────────────────────────────

  // Chapter (level 1): right-aligned, two-line display (label above, title below)
  show heading.where(level: 1): it => {
    v(1.5em)
    if it.numbering != none {
      align(right, text(size: 12pt, weight: "regular")[
        Chapter #counter(heading).display(it.numbering)
      ])
      v(0.15em)
    }
    align(right, text(size: 28pt, weight: "bold")[#smallcaps(it.body)])
    v(20pt)
  }

  // Section (level 2): bold small-caps with rule below
  show heading.where(level: 2): it => {
    v(0.8em)
    block(width: 100%)[
      #text(size: 14pt, weight: "bold")[
        #if it.numbering != none {
          smallcaps(counter(heading).display(it.numbering))
          h(0.5em)
        }
        #smallcaps(it.body)
      ]
      #v(4pt)
      #line(length: 100%, stroke: 0.5pt)
    ]
    v(0.4em)
  }

  // Subsection (level 3): bold small-caps
  show heading.where(level: 3): it => {
    v(0.5em)
    text(size: 12pt, weight: "bold")[
      #if it.numbering != none {
        smallcaps(counter(heading).display(it.numbering))
        h(0.5em)
      }
      #smallcaps(it.body)
    ]
    v(0.2em)
  }

  // Subsubsection (level 4)
  show heading.where(level: 4): it => {
    v(0.3em)
    text(size: 11pt, weight: "bold")[
      #if it.numbering != none {
        smallcaps(counter(heading).display(it.numbering))
        h(0.5em)
      }
      #smallcaps(it.body)
    ]
    v(0.1em)
  }

  // Table captions go above the table (typographic convention)
  show figure.where(kind: table): set figure.caption(position: bottom)

  // All figure captions in italics
  show figure.caption: set text(style: "italic")

  // req(), user-story(), and use-case() render as plain blocks - strip the figure centering/padding wrapper
  show figure.where(kind: "req"):              it => it.body
  show figure.where(kind: "user-story"):       it => it.body
  show figure.where(kind: "use-case"):         it => it.body
  show figure.where(kind: "scenario"):         it => it.body
  show figure.where(kind: "risk"):              it => it.body
  show figure.where(kind: "risk-contingency"):  it => it.body
  show figure.where(kind: "opportunity"):       it => it.body
  show figure.where(kind: "opportunity-action"): it => it.body


  show ref: it => {
    let el = it.element
    let card-kinds = ("req", "user-story", "use-case", "scenario", "risk", "risk-contingency",
      "opportunity", "opportunity-action")
    if el != none and el.has("kind") and card-kinds.contains(el.kind) {
      link(it.target)[#el.supplement]
    } else {
      it
    }
  }

  body
}
