# Helpers API

!!! info "Overview"
    The Helpers API provides utility functions to partition work across replicas of a CANFAR session. Containers receive `REPLICA_ID` and `REPLICA_COUNT` environment variables, and these helpers make using them simple and correct.

## Practical Examples

### Stripe: take every Nth item with an offset
```python
from canfar.helpers import distributed

# Assume REPLICA_ID=2 and REPLICA_COUNT=4
# Replica 2 (1-based) will see indices 1, 5, 9, ...
items = list(range(12))
shard = list(distributed.stripe(items, replica=2, total=4))
print(shard)  # [1, 5, 9]
```

### Chunk: contiguous chunks of roughly equal size
```python
from canfar.helpers import distributed

# Assume 10 items, 4 replicas
items = list(range(10))
# Replica 1 gets [0,1], 2->[2,3], 3->[4,5], 4->[6,7,8,9] (last takes remainder)
print(list(distributed.chunk(items, replica=1, total=4)))
print(list(distributed.chunk(items, replica=4, total=4)))
```

!!! note "Sparse distribution"
    When items < replicas, `chunk` assigns exactly one item to each of the first `len(items)` replicas, and later replicas get nothing. This avoids duplication.

### Using container-provided environment variables
```python
# Inside CANFAR container replicas, you can omit replica/total and read from env
from canfar.helpers import distributed
work = list(range(1000))
for item in distributed.chunk(work):
    process(item)
```

### Validation and errors
- `replica` must be >= 1 and <= `total`
- `total` must be > 0

## API Reference

::: canfar.helpers.distributed
    handler: python
    options:
      members:
        - stripe
        - chunk
      show_root_heading: true
      show_source: false
      heading_level: 3
      docstring_style: google
      show_signature_annotations: true