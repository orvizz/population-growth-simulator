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
  
  // Simple Cover Page
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
  outline(depth: 3, indent: auto)
  pagebreak()
  
  // Main Content
  set par(justify: true)
  body
} 