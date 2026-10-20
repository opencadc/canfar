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
server; common keys include `cores`, `memoryGB`, `gpus`, and
`maxInteractiveSessions`. Resource limits are server metadata, not a second
Configuration model: Server discovery reads this payload with
`ServerResources.from_context()` and saves the result as each Server's
`resources`.

```python
from canfar.context import Context
from canfar.models.http import ServerResources

with Context() as context:
    resources = ServerResources.from_context(context.resources())
    print(resources.flexible.cores)  # guaranteed request to burst limit
    print(resources.fixed.ram)  # smallest to largest fixed memory, in GB
```

A value the Server does not advertise is `None`. `from_context()` raises
`ValueError` when the payload holds no limit it recognizes, as from older
platform versions.

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

::: canfar.models.http.ServerResources
    handler: python
    selection:
      members:
        - from_context
    rendering:
      members_order: source
      show_root_heading: true
      show_source: false
      heading_level: 2
