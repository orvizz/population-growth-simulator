#let project(title: "", author: "", first_tutor: "", second_tutor: "", body) = {
  // Document setup
  set document(title: title, author: author)
  set page(
    paper: "a4",
    margin: (x: 3cm, y: 3cm),
    numbering: "1",
    number-align: center,
  )

  // Text rules
  set text(font: "Linux Libertine", size: 11pt, lang: "en")
  set heading(numbering: "1.1.")
  show heading: set block(above: 1.4em, below: 1em)
/*
  // Cover page
  page(numbering: none)[
    // University logo top-left
    image("resources/logo_uniovi.png", width: 35%)

    v(1fr)

    // Title block
    line(length: 100%, stroke: 0.5pt)
    v(0.6em)
    text(weight: "bold", size: 22pt)[#title]
    v(0.6em)
    line(length: 100%, stroke: 0.5pt)

    v(2em)

    // Metadata grid
    grid(
      columns: (120pt, 1fr),
      row-gutter: 0.6em,
      text(fill: luma(120), size: 10pt)[Author],
      text(size: 10pt)[#author],
      text(fill: luma(120), size: 10pt)[Supervisors],
      text(size: 10pt)[#first_tutor #linebreak() #second_tutor],
      text(fill: luma(120), size: 10pt)[Degree],
      text(size: 10pt)[Software Engineering],
      text(fill: luma(120), size: 10pt)[University],
      text(size: 10pt)[University of Oviedo],
      text(fill: luma(120), size: 10pt)[Date],
      text(size: 10pt)[#datetime.today().display("[month repr:long] [year]")],
    )

    v(1fr)
  ]*/

  align(center)[
    #image("resources/logo_uniovi.png", width: 40%) // Ensure you have the logo file
    #v(2em)
    #text(weight: "bold", size: 20pt)[#title]
    #v(1em)
    #text(size: 14pt)[#author]
    #v(2em)
    #grid(
      columns: (1fr),
      gutter: 1em,
      [Degree: Software Engineering],
      [Tutor: \ #first_tutor \ #second_tutor],
      [#datetime.today().display("[month repr:long] [year]")]
    )
  ]

  pagebreak()

  // Table of Contents
  outline(depth: 2, indent: auto)
  pagebreak()

  // Main Content
  set par(justify: true)
  body
}
