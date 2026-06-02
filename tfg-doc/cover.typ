// cover.typ — title page
// Layout: logos → v(1fr) → info block → v(1fr) → footer
// All major gaps use v(1fr) so the cover always fills exactly one page.
#import "metadata.typ": tfg-title, tfg-type, tfg-author, tfg-tutor-a, tfg-tutor-b, tfg-year, tfg-version, tfg-date, tfg-location

#grid(
  columns: (1fr, 1fr),
  align(left,  image("resources/logos/uniovi_logo.png", height: 4cm)),
  align(right, image("resources/logos/eii_logo.png",   height: 4cm)),
)

#v(1fr)

#align(center)[
  #text(size: 18pt)[#upper[Degree in Software Engineering]]

  #v(1em)
  #text(size: 13pt)[*Type of TFG:* #tfg-type]

  #v(0.5em)
  #text(size: 13pt)[*Year:* #tfg-year]

  #v(2em)
  #text(size: 22pt, weight: "bold")[#tfg-title]

  #v(2em)
  #text(size: 16pt)[*Author:* #tfg-author]

  #v(0.8em)
  #text(size: 16pt)[*Tutors:* #tfg-tutor-a]

  #v(0.4em)
  #text(size: 16pt)[#tfg-tutor-b]
]

#v(1fr)

#align(center,
  text(size: 9pt)[Version #tfg-version (#tfg-date) #h(1em) #tfg-location]
)
