# TYPST POLICY

This file contains the policy for organizing the internal file structure of any typst project. The things specified here are MANDATORY. 

## Main project files

- `./main.typ`: This file works as an orchestator. Is the file that puts all together.
- `./template.typ`: This file contains the styles of the project. Every single style of the project will live exclusively inside this file. In this file, not only style but also functions to create different kinds of components can be specified (like, defining an special block or an special table). If the functions get too large, they must be extracted to a file called `./utils.typ`, to keep this file not too large and readable.
- `./cover.typ`: In this file, we must specify the cover of the document.
- `./backcover.typ` (optional): If we want a backcover, it must be created in this file.
- `./metadata.typ`: This file will contain information taht will be reused many times in the project, so, if we need to change something, we have only to do it in one place. Here, some variables like `author` can be specified.
- `./sources.bib`: Bibliography file. All bibliographic references must be places inside here.

This files contain the baseline for any document. They are the core of the typst project.

## Chapters

Al the content of the document will be placed inside the `./chapters/` directory. 

The `./chapters/` folder will contain one subfolder for each chapter:

```
main.typ
template.typ
...
chapters/
|    chapter1/ (folder naming does not have to be as satrict as chapter 1, chapter 2... We can put the number and the name of the chapter)
|   |   <whatever files>
|   chapter2/
|   |
...
```

Each chapter or section owns its own file, and each chapter manges is subsections by itself. This means that, in the `./main.typ` file, we'll only link once a chapter, and it'll be responsability of each chapter to orchestate their own sections. 

>Important:  
>  Tables are more easy to modify if we group in a single file all the tables of each chapter. This means, tables are defined in a single `./chapters/<chapterFolder>/tables.typ`, and linked in the .typ files that require them. 

## Resources

All the resources of the document, for example, images or diagrams, will be placed inside of the `./resources` folder. There's no need to strictly separate them into folders, but it could be useful to create directories with comprenhensive names, like, the name of the chapters where those resorces will be used or a shared folder with resourcees that will be shared between chapters. 
The main resources, like logos or so, can have their own directory inside the `./resources` directory.

## Cover Page

The cover page (`./cover.typ`) **must always occupy exactly one page**. No content may overflow onto a second page. The same rule applies to `./backcover.typ`.

To guarantee this:
- Never use fixed vertical spacing between cover elements. Use `#v(1fr)` (flexible space) to distribute content proportionally within the available page height, regardless of small content changes.
- The typical layout is: logo area → `#v(1fr)` → title block → `#v(1fr)` → footer info.
- As a safety measure, the cover's outer block may use `clip: true` to prevent accidental overflow from appearing silently on a second page.

## Figures and Tables

Every image, table, diagram, or chart that appears in the document **must** be wrapped in a `#figure(caption: [...])` block. Bare tables or images without a figure wrapper are forbidden — they won't be collected by the List of Figures / List of Tables outlines.

`main.typ` must include outline calls for both kinds:

```typst
#outline(title: "List of Figures", target: figure.where(kind: image))
#outline(title: "List of Tables",  target: figure.where(kind: table))
```

If custom figure kinds are introduced (e.g., code listings with `kind: "listing"`), a dedicated `#outline(target: figure.where(kind: "listing"))` must be added as well.

**Caption placement convention** (typographic standard):
- Table captions go **above** the table.
- Image and diagram captions go **below** the figure.

Because Typst places captions below by default, `template.typ` must contain the following show rule inside the `template(body)` function:

```typst
show figure.where(kind: table): set figure.caption(position: top)
```

## Cross-References

Every figure, table, and section heading that may be referenced elsewhere in the document **must** carry a `<label>`. Labels follow a strict namespace convention to avoid collisions:

| Prefix | Applies to          |
|--------|---------------------|
| `fig:` | Figures (images, diagrams) |
| `tab:` | Tables              |
| `sec:` | Section headings    |
| `eq:`  | Equations           |
| `lst:` | Code listings       |
| `req:` | Requirements        |

Always use `@label` syntax to refer to labelled elements — never hardcode numbers or names. Typst renders `@label` as a clickable hyperlink in the exported PDF.

```typst
// Label a heading
= Introduction <sec:intro>

// Label a figure (must be in markup mode — wrap #let content in [...])
#let my-fig = [
  #figure(image("..."), caption: [Caption text]) <fig:my-fig>
]

// Cross-reference it
As shown in @fig:my-fig, ...   // → clickable "Figure 1"
See @sec:intro for background. // → clickable "Section 1"
```

> **Important:** `<label>` syntax is only valid in markup mode. Inside a `#let` binding, wrap the entire figure in `[...]` to switch to markup mode before placing `<label>`. See the existing tables in `chapters/*/tables.typ` for examples.

## PDF Metadata and Bookmarks

`main.typ` must set PDF document metadata **before any content is output**:

```typst
#set document(
  title:  tfg-title,
  author: tfg-author,
  date:   auto,
)
```

`tfg-title` and `tfg-author` are imported from `metadata.typ`.

Typst automatically creates PDF bookmarks from all headings. This behaviour must **not** be disabled globally (`set heading(bookmarked: false)` is forbidden at document scope). Front matter headings may optionally suppress their bookmark locally if they would clutter the bookmark panel, but keeping them bookmarked is the default.

## Additional Good Practices

- **No orphan headings.** A heading must never appear alone at the bottom of a page with no following content. Use `block(breakable: false)` or restructure content to prevent this.
- **External links.** Use `#link(url)[descriptive text]` — never paste bare URLs into prose. The link text must describe the destination.
- **Soft page breaks.** Use `#pagebreak(weak: true)` before `#include` calls in `main.typ`. A weak break is suppressed if a hard break already exists, preventing double blank pages.
- **Heading depth.** Never skip heading levels (e.g., do not jump from `=` directly to `===`). Maximum recommended TOC depth: 3 levels.
- **Bibliography.** All references live in `sources.bib` and are cited via `@key`. Never hardcode reference numbers or author names inline.
- **Color contrast.** When using colored table fills, ensure sufficient contrast for readability. Do not rely on color alone as the sole visual differentiator — add labels or patterns when necessary.
- **Code blocks.** Use Typst `raw()` or backtick syntax for all inline code and listings. Never use bold or italic to represent code.
- **Non-breaking spaces.** Use `~` (tilde) for spaces that must not break across lines, e.g. `Table~3` in free text (though `@label` handles this automatically for labelled elements).