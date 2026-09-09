# Overview API

`Overview` checks whether a Science Platform Server reports itself as
available. It inherits `HTTPClient` and uses the selected or explicitly supplied
credentials.

```python
from canfar.overview import Overview

with Overview() as overview:
    if overview.availability():
        print("Science Platform Server is available")
```

`availability()` returns `True` only when the VOSI availability response says
the server is available. Empty or malformed availability data returns `False`
and is logged.

::: canfar.overview.Overview
    handler: python
    selection:
      members:
        - availability
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
