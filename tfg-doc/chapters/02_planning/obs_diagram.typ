// chapters/02_planning/obs_diagram.typ
// OBS tree diagram wrapped in [...] so <fig:obs> label is in markup mode
#import "../../template.typ": obs-node

#let obs-diagram = [
  #figure(
    {
      set text(size: 10pt)

      // Root node
      align(center,
        block(width: 65%,
          obs-node(fill: rgb(50, 50, 50))[
            #text(fill: white, weight: "bold", size: 11pt)[TFG Project] \
            #text(fill: luma(190), size: 9pt)[Population Growth Simulator]
          ]
        )
      )

      v(8pt)

      grid(
        columns: (1fr, 1fr),
        gutter:  14pt,

        // ── Left branch: Project Executor ──────────────────────────────────
        {
          obs-node(fill: rgb(188, 210, 238))[
            #text(weight: "bold")[SI-6: Mario Orviz Viesca] \
            #text(size: 9pt)[Project Executor]
          ]
          v(4pt)
          for (id, label) in (
            ("1.1", "Planning & Definition"),
            ("1.2", "Analysis & Design"),
            ("1.3", "Development & Testing"),
            ("1.4", "Documentation & Closure"),
          ) {
            obs-node(fill: rgb(219, 229, 241))[
              #text(size: 9pt)[*#id* — #label]
            ]
            v(3pt)
          }
        },

        // ── Right branch: Supervision Panel ────────────────────────────────
        {
          obs-node(fill: luma(210))[
            #text(weight: "bold")[Supervision & Acceptance Panel]
          ]
          v(4pt)
          obs-node(fill: luma(228))[
            #text(size: 9pt)[SI-4: Celia Melendi Lavandera] \
            #text(size: 8pt)[Software Eng. Tutor]
          ]
          v(3pt)
          obs-node(fill: luma(228))[
            #text(size: 9pt)[SI-5: Mario Quevedo de Anta] \
            #text(size: 8pt)[Biology Co-tutor]
          ]
        },
      )
    },
    caption: [Organizational Breakdown Structure (OBS)],
  ) <fig:obs>
]
