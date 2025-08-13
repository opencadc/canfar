# Context API

!!! info "Overview"

    The Context API allows the user to get information about the resources available to be requested for a session on the CANFAR Science Platform. This information can be used to configure the session to request the appropriate resources for your session.

```python title="Get context information"
from canfar.context import Context

context = Context()
context.resources()
```

```python
{
    "cores": {
        "default": 1,
        "defaultRequest": 1,
        "defaultLimit": 16,
        "defaultHeadless": 1,
        "options": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    },
    "memoryGB": {
        "default": 2,
        "defaultRequest": 4,
        "defaultLimit": 192,
        "defaultHeadless": 4,
        "options": [1, 2, ..., 192],
    },
    "gpus": {
        "options": [1, ..., 8],
    },
}
```

::: canfar.context.Context
    handler: python
    selection:
      members:
        - resources
    rendering:
      members_order: source
      show_root_heading: true
      show_source: true
      heading_level: 3
