// Compile from the repository root:
// typst compile docs/presentations/canfar-data-operations-blue-professional.typ /tmp/canfar-data-operations.pdf
// Keep generated PDFs and images outside the source tree.

#set document(title: "CANFAR Data Operations", author: "Shiny Brar · Team Coral")

#let blue = rgb("1e2bfa")
#let ink = rgb("111111")
#let muted = rgb("626777")
#let paper = rgb("fdfae7")
#let panel = rgb("f0f1ff")

#set page(
  width: 320mm,
  height: 180mm,
  margin: (x: 16mm, top: 13mm, bottom: 16mm),
  fill: paper,
  footer: context align(right, text(size: 10pt, fill: muted)[
    #counter(page).display("1 / 1", both: true)
  ]),
)
#set text(font: "Libertinus Serif", size: 16pt, fill: ink, lang: "en")
#set par(leading: 0.6em, spacing: 0.7em)
#set heading(numbering: none)
#show heading.where(level: 1): set text(size: 30pt, weight: "bold")
#show heading.where(level: 1): set block(above: 0pt, below: 3mm)
#show heading.where(level: 2): set text(size: 19pt, weight: "bold")
#show link: set text(fill: blue)
#show raw: set text(font: "DejaVu Sans Mono", size: 11pt)

#let slide(title, eyebrow: none, tag: none, body) = {
  pagebreak(weak: true)
  if eyebrow != none {
    grid(
      columns: (1fr, auto),
      align: (left, right),
      text(size: 11pt, weight: "bold", fill: blue, eyebrow),
      text(size: 11pt, fill: blue, if tag != none { tag }),
    )
    v(7mm)
  }
  heading(level: 1, title)
  v(3mm)
  body
}

#let card(number, title, body) = block(
  width: 100%,
  height: 53mm,
  inset: 5mm,
  radius: 3mm,
  fill: panel,
)[
  #text(size: 17pt, weight: "bold", fill: blue, number)
  #v(2mm)
  #text(size: 16pt, weight: "bold", title)
  #v(2mm)
  #text(size: 14pt, body)
]

#let highlight(body) = block(
  width: 100%,
  inset: 5mm,
  radius: 3mm,
  fill: panel,
  stroke: (left: 2pt + blue),
  body,
)

// 1. Title
#v(24mm)
#text(size: 14pt, weight: "bold", fill: blue)[CADC]
#v(7mm)
#text(size: 46pt, weight: "bold")[CANFAR Data Operations]
#v(7mm)
#line(length: 23mm, stroke: 2pt + blue)
#v(7mm)
#text(size: 25pt)[The missing data layer.]
#v(13mm)
#text(size: 15pt, fill: muted)[Shiny Brar · Team Coral]

// 2. fsspec + vosfs
#slide(
  [fsspec: One File System API],
  eyebrow: [The standard],
  tag: [fsspec],
)[
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 5mm,
    card([1], [A Python standard])[
      One filesystem interface. Not a CANFAR invention. Scientific Python already knows it.
    ],
    card([2], [Many backends])[
      S3, GCS, HTTP, local — same *ls*, *open*, *cat_file*.
    ],
    card([3], [Already in the stack])[
      numpy, Astropy, and pandas already speak it.
    ],
  )
  #v(5mm)
  #highlight[
    #text(size: 11pt, weight: "bold", fill: blue)[The core goal]
    #v(2mm)
    #text(size: 26pt, weight: "bold")[vosfs]
    #v(2mm)
    Implement VOSpace as an fsspec filesystem. A VOSpace node is another backend, not a special protocol.
  ]
  #v(4mm)
  #link("https://github.com/shinybrar/vosfs")[github.com/shinybrar/vosfs]
]

// 3. fsspec-cli + claim
#slide(
  [One CLI across identity providers.],
  eyebrow: [The front door],
  tag: [canfar data],
)[
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 5mm,
    card([1], [Any number of filespecs])[
      An SRCNet node can expose several fsspec backends. We did not want a new CLI per store.
    ],
    card([2], [Any identity])[
      CADC is X.509. SRCNet is OIDC. The Storage Identifier selects the Authentication Record.
    ],
    card([3], [The claim])[
      CANFAR is one CLI across identity providers, for any storage that speaks fsspec.
    ],
  )
  #v(5mm)
  #highlight[
    #text(size: 11pt, weight: "bold", fill: blue)[POSIX for any fsspec]
    #v(2mm)
    #text(size: 26pt, weight: "bold")[fsspec-cli]
    #v(2mm)
    Turns any fsspec into a POSIX-like experience: *ls*, *cp*, *head*, *rm*. *canfar data* is that CLI with your logins already wired.
  ]
  #v(4mm)
  #text(fill: blue)[uv run canfar data]
]

// 4. Live
#slide(
  [Copy CADC to Sweden. Same command.],
  eyebrow: [Live],
  tag: [arc → sweSRC],
)[
  #block(width: 100%, fill: panel, radius: 3mm, inset: 6mm)[
    #set par(leading: 1.2em)
    ```sh
    $ uv run canfar data ls arc:/home/brars
    $ uv run canfar data head -c 1000 arc:/home/brars/find-uid-gid-mismatch.sh
    $ uv run canfar data cp arc:/home/brars/find-uid-gid-mismatch.sh sweSRC:/home/shinybrar/
    $ uv run canfar data head -c 1000 sweSRC:/home/shinybrar/find-uid-gid-mismatch.sh
    $ uv run canfar data rm sweSRC:/home/shinybrar/find-uid-gid-mismatch.sh
    ```
  ]
  #v(7mm)
  #highlight[
    *Before cp:* *arc* is CADC (X.509). *sweSRC* is SRCNet (OIDC). You are not switching servers.
  ]
]

// 5. Python
#slide(
  [Open it from any compute instance.],
  eyebrow: [Python API],
  tag: [any SRCNet container],
)[
  #block(width: 100%, fill: panel, radius: 3mm, inset: 5mm)[
    #set par(leading: 0.4em)
    ```python
    from astropy.io import fits
    from fsspec.implementations.cached import SimpleCacheFileSystem
    import numpy as np
    from canfar.storage import filesystem

    remote = filesystem("sweSRC")
    try:
        fs = SimpleCacheFileSystem(fs=remote, cache_storage="/scratch/canfar-swesrc")
        with fs.open("/project/array.npy", "rb") as handle:
            array = np.load(handle, allow_pickle=False)
        with fs.open("/project/cube.fits", "rb") as handle:
            with fits.open(handle) as hdul:
                image = hdul[0].data
    finally:
        remote.close()
    ```
  ]
  #v(4mm)
  #text(size: 13pt, fill: muted)[
    Same file, any SRCNet container. Cache is opt-in. Close the VOSpace client (remote), not only the wrapper.
  ]
]

// 6. Close
#pagebreak()
#v(30mm)
#align(center)[
  #text(size: 13pt, weight: "bold", fill: blue)[Take home]
  #v(8mm)
  #text(size: 38pt, weight: "bold")[One data layer across SRCNet.]
  #v(7mm)
  #line(length: 23mm, stroke: 2pt + blue)
  #v(7mm)
  #text(size: 21pt, fill: muted)[One CLI. Any identity. Any storage that speaks fsspec.]
  #v(12mm)
  #block(fill: blue, radius: 3mm, inset: (x: 10mm, y: 4mm))[
    #text(size: 17pt, weight: "bold", fill: white)[Questions]
  ]
]
