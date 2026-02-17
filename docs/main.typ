#import "template.typ": project
#import "metadata.typ": *

#show: project.with(
  title: title,
  author: author,
  first_tutor: first_tutor,
  second_tutor: second_tutor,
)

// Include your chapters here
#include "chapters/introduction.typ"
//#include "chapters/state-of-the-art.typ"
// #include "chapters/implementation.typ"