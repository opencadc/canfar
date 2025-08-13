# Images API

!!! info "Overview"
    The Image API allows you to get information about the **publicly available** images on the CANFAR Science Platform through the CANFAR Harbor Registry. It can be used to get information about all images, or filter by a specific image kind.

## Getting Image Information

```python title="Get image information"
from canfar.images import Images

images = Images()
images.fetch()
[
    "images.canfar.net/canfar/base-3.12:v0.4.1",
    "images.canfar.net/canucs/test:1.2.5",
    "images.canfar.net/canucs/canucs:1.2.9",
    ...,
]
```

But most of the time, you are only interested in images of a particular type. For example, if you want to get all the images that are available for `headless` sessions, you can do the following:

```python title="Get headless image information"
images.fetch(kind="headless")
```

```python
[
    "images.canfar.net/chimefrb/testing:keep",
    "images.canfar.net/lsst/lsst_v19_0_0:0.1",
    "images.canfar.net/skaha/lensfit:22.11",
    "images.canfar.net/skaha/lensfit:22.10",
    "images.canfar.net/skaha/lensingsim:22.07",
    "images.canfar.net/skaha/phosim:5.6.11",
    "images.canfar.net/skaha/terminal:1.1.2",
    "images.canfar.net/skaha/terminal:1.1.1",
    "images.canfar.net/uvickbos/pycharm:0.1",
    "images.canfar.net/uvickbos/swarp:0.1",
    "images.canfar.net/uvickbos/isis:2.2",
    "images.canfar.net/uvickbos/find_moving:0.1",
]
```

## API Reference

::: canfar.images.Images
    handler: python
    selection:
      members:
        - fetch
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 3
