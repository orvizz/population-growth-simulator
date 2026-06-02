// chapters/00_disclaimer/index.typ
#import "../../template.typ": guia

= Important Notes on this Template

#guia[
  *VERY IMPORTANT NOTE:* This template is only an *orientative guide*. A Final
  Degree Project (TFG) does not necessarily have to include all these sections, nor
  only those that appear here; it depends on the specific characteristics of each
  project.

  *USING THIS TEMPLATE IS NOT MANDATORY AT ALL* for completing a TFG; it is only an
  optional aid if the tutor or student wishes to use it.

  The template must be adapted to each project (adding sections, removing some, or
  modifying the contents as needed for each particular case). The student must always
  consult their director, whose instructions *ALWAYS* take priority over any doubts
  regarding any topic.

  This template has been prepared thanks to the help of Pablo Javier Tuya González,
  professor in charge of the subjects _Software Process Engineering_ and _Software
  Quality, Validation, and Verification_, as well as other professors such as Raúl
  Izquierdo, Aquilino Fuente, Benjamín López, Jose Emilio Labra, etc., who provided
  feedback on the parts related to their subjects. Your decisions must be consistent
  with what is taught in these subjects and others applicable to each part of the
  developed project (e.g., _Project Management and Planning_, _Computer System
  Security_, _Databases_, _Programming Language Design_, etc.). Some of these are
  explicitly mentioned in various sections of this document.

  Although this document is provided as a guide, nothing prevents using it only as a
  point-of-reference guide and generating the documentation automatically in various
  formats following the *"Documentation as Code"* philosophy learned during the
  degree. You do not have to use Word; other formats like *Typst*, *LaTeX*, etc., are
  perfectly possible.

  *WE REITERATE THAT THE USE OF THIS DOCUMENT IS NOT MANDATORY*, and the content of
  *RELATED SUBJECTS WILL ALWAYS PREVAIL* over what is stated here. The idea of this
  document is to serve as an *AID*, NOT as a *RULE*.

  This document may contain errors. If you wish to collaborate to improve it, please
  send an email with your issues to `redondojose` at the Uniovi email domain. THANK
  YOU.
]

#guia[
  == Aspects to consider for your TFG documentation:

  - #guia[The explanatory text for the template parts is in brown and *MUST DISAPPEAR
    COMPLETELY* from the final version. For your own text, use black color. Leaving
    template text in the TFG documentation will have a significant negative impact on
    your grade, as it indicates a lack of care in your work.]

  - *Images and Tables:* To ensure they are included in the indices, use the
    `#figure(...)` function. It is recommended to centre them and ensure they are
    legible and of high quality. To respect copyrights, *always cite the source (URL)*
    from which they were obtained. You can add it at the end of the caption (e.g.,
    "Source: \<URL\>").

  - *Hyperlinks and Navigation:* When generating the final PDF, ensure that bookmarks
    are generated so the resulting document is navigable in a PDF viewer, facilitating
    the tribunal's work.

  - *Digital Quality:* Generate the PDF directly (Export/Save as) instead of
    "Printing to PDF" to ensure that internal document links and external URLs remain
    clickable.

  - *Spelling and Grammar:* Always run the spell checker at the end and check for
    grammatical errors. Failing to do so diminishes the quality of your work.

  - *Research Component:* If your project has a strong research character, there is a
    specific template for research projects for the Master's in Web Engineering. It can
    be combined with this one if your development project includes a research component.
]

#v(1cm)

#figure(
  image("../../resources/logos/uniovi_logo.png", width: 50%),
  caption: [Example of a figure with a citation. Use "Figure" or "Illustration"
            consistently throughout the document.
            Source: #link("https://www.uniovi.es")[www.uniovi.es]],
) <fig:disclaimer-example>
