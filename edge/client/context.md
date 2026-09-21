# Context API

`Context` reads the resource information advertised by a Science Platform
Server. The returned mapping can guide `Session.create()` resource requests.

```python
from canfar.context import Context

with Context() as context:
    resources = context.resources()
    print(resources["cores"])
    print(resources.get("memoryGB"))
    print(resources.get("gpus"))
```

The response is a `dict[str, Any]` whose keys and values are supplied by the
server; common keys include `cores`, `memoryGB`, and `gpus`. Resource limits are
server metadata, not a second Configuration model.

::: canfar.context.Context
    handler: python
    selection:
      members:
        - resources
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 2
