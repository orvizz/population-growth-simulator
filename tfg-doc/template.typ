// template.typ — all styles, layout rules, and reusable component functions
#import "metadata.typ": tfg-title, tfg-author

// ── Colours ───────────────────────────────────────────────────────────────────
#let uniovi-blue = rgb(0, 172, 233)
#let guia-color  = rgb(139, 69, 19)

// ── Utility functions ─────────────────────────────────────────────────────────

// Brown italic placeholder text — must be removed in the final version
#let guia(content) = text(fill: guia-color, style: "italic")[#content]

// ── Requirement counter and prefix state ─────────────────────────────────────
#let _req-c      = counter("req")
#let _req-prefix = state("req-prefix", "SR")

// Call before each requirement block to set the prefix (e.g. "SR-F", "SR-NF")
// and reset the counter so numbering starts from 01.
#let req-group(prefix) = {
  _req-prefix.update(prefix)
  _req-c.update((0, 0, 0))
}

// Auto-numbered requirement item.
//   indent 0 → top level:  SR-F-01
//   indent 1 → sub-req:    SR-F-01.1
//   indent 2 → leaf:       SR-F-01.1.1
// Each item gets a label <req:sr-f-01.1.1> for cross-referencing via @req:...
#let req(title, content, indent: 0) = {
  _req-c.step(level: indent + 1)
  context {
    let pfx  = _req-prefix.get()
    let nums = _req-c.get()
    let p2(n) = if n < 10 { "0" + str(n) } else { str(n) }
    let id = pfx + "-" + p2(nums.at(0, default: 1)) + (if indent >= 1 { "." + str(nums.at(1, default: 1)) } else { "" }) + (if indent >= 2 { "." + str(nums.at(2, default: 1)) } else { "" })
    [#figure(
      align(left, pad(left: indent * 1em, block(below: 0.5em)[*#id* — *#title* #content])),
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
    header: align(center, image("resources/logos/eii_header.png", height: 2cm)),
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

  // req() and user-story() render as plain blocks — strip the figure centering/padding wrapper
  show figure.where(kind: "req"):         it => it.body
  show figure.where(kind: "user-story"):  it => it.body


  show ref: it => {
    let el = it.element
    if el != none and el.has("kind") and (el.kind == "req" or el.kind == "user-story") {
      link(it.target)[#el.supplement]
    } else {
      it
    }
  }

  body
}
