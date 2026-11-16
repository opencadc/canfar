# Helpers API

!!! info "Overview"
    `canfar.helpers.distributed` partitions an ordered list across replicas.
    A [batch](../platform/sessions/batch.md#run-many-replicas-as-one-batch)
    replica receives a 0-based `CANFAR_REPLICA_INDEX` and
    `CANFAR_REPLICA_COUNT`; a deprecated headless replica receives a 1-based
    `REPLICA_ID` and `REPLICA_COUNT`. These functions read them by default.
    Their `replica` argument stays 1-based: `CANFAR_REPLICA_INDEX=0` is
    replica 1.

## Practical examples

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
# Inside a batch replica, omit replica/total to read them from the environment
from canfar.helpers import distributed
work = list(range(1000))
for item in distributed.chunk(work):
    process(item)
```

### Validation and errors

`chunk()` requires `total > 0` and `1 <= replica <= total`, raising
`ValueError` otherwise. `stripe()` intentionally keeps a looser compatibility
contract: `replica < 1` yields no items, even when `total <= 0`. For a positive
replica, `total <= 0` raises `ValueError`; otherwise `replica > total` yields
no items. When `replica` is omitted, both functions use
`CANFAR_REPLICA_INDEX` plus 1, otherwise `REPLICA_ID`. When `total` is
omitted, they use `CANFAR_REPLICA_COUNT`, otherwise `REPLICA_COUNT`. Without
any of them, the worker acts as the only replica, so the same script runs
unchanged in a local test.

A batch replica can run again from the beginning after preemption or a node
drain. Make each item's work safe to repeat, for example by skipping items
whose output already exists.

## API reference

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
