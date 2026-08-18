# Container Images API

`Images` lists the Container Images advertised by a CANFAR Science Platform
Server. It inherits `HTTPClient`, so the same saved or runtime credential
selection applies.

## Image identifiers

```python
from canfar.images import Images

with Images() as images:
    all_images = images.fetch()                 # list[str]
    headless = images.fetch(kind="headless")   # list[str]
    print(headless)
```

Each string is an image identifier such as
`images.canfar.net/skaha/terminal:latest`. The optional `kind` is sent as the
server's image-type filter.

## Parsed image details

Use `details()` when the digest and supported kinds are needed:

```python
from canfar.images import Images

with Images() as images:
    for image in images.details():
        print(image.id, image.types, image.digest)
```

`details()` returns `list[canfar.models.containers.Image]`; each model has `id`,
`types`, and `digest` fields.

## API Reference

::: canfar.images.Images
    handler: python
    selection:
      members:
        - fetch
        - details
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 3
