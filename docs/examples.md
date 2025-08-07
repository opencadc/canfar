# Skaha Usage Examples

## Creating a Session

```python title="Create a session"
from skaha.session import Session

session = Session()
session_ids = session.create(
    name="test",
    image="images.canfar.net/skaha/terminal:1.1.1",
    cores=2,
    ram=8,
    kind="headless",
    cmd="env",
    env={"TEST": "test"},
    replicas=3,
)
```

This will create three headless containers, each with 2 cores and 8GB of RAM, and run the command `env` in each container. The environment variable `TEST` will be set to `test` in each container. The response will be a list of session IDs created.

```python
print(session_ids)
["mrjdtbn9", "ov6doae7", "g9b4p1p4"]
```

!!! tip "Container Replicas"
    When spawning sessions with the Skaha API, it adds two additional environment variables to each container:

    - `REPLICA_COUNT`: An integer representing the total number of replicas spawned, e.g. 3 for the example above.
    - `REPLICA_ID`: An integer representing the unique ID of the replica using **1-based indexing**, e.g. 1, 2, 3 for the example above.

    These environment variables can be used to configure your application to run in a distributed manner. The Skaha distributed helpers (`chunk` and `stripe`) automatically handle the conversion from 1-based REPLICA_ID values to appropriate data partitioning. For example, you can use the `REPLICA_COUNT` to configure the number of workers and the `REPLICA_ID` to configure the rank of the worker.

!!! warning "Private Container Registry Access"
    If you are using a private container image from the CANFAR Harbor Registry, you need to provide your harbor `username` and the `CLI Secret` through a `ContainerRegistry` object.
    ```python
    from skaha.models import ContainerRegistry
    from skaha.session import Session

    registry = ContainerRegistry(username="username", password="sUp3rS3cr3t")
    session = Session(registry=registry)
    ```

## Getting Session Information

```python title="Get session information"
session.info(session_id)
```

```bash title="Session Information"
[{'id': 'g9b4p1p4',
  'userid': 'brars',
  'runAsUID': '166169204',
  'runAsGID': '166169204',
  'supplementalGroups': [34241, 34337, 35124, 36227, 1454823273, 1025424273],
  'appid': '<none>',
  'image': 'images.canfar.net/skaha/terminal:1.1.1',
  'type': 'headless',
  'status': 'Pending',
  'name': '2a74d03-1',
  'startTime': '2024-10-21T21:39:01Z',
  'expiryTime': '2024-11-04T21:39:01Z',
  'connectURL': 'not-applicable',
  'requestedRAM': '1G',
  'requestedCPUCores': '1',
  'requestedGPUCores': '0',
  'ramInUse': '<none>',
  'gpuRAMInUse': '<none>',
  'cpuCoresInUse': '<none>',
  'gpuUtilization': '<none>'}]
```

## Getting Deployment Information

Deployment information, about that events that occurred during the deployment of a session, can be retrieved using the `events` method.

```python title="Get deployment information"
events = session.events(session_ids, verbose=True)
```

```
TYPE     REASON      MESSAGE                                                                                              FIRST-TIME             LAST-TIME
Normal   Scheduled   Successfully assigned skaha-workload/skaha-headless-user-gvfusmzo-kdqkz to keel-prod-k8s-node-x04   <nil>                  <nil>
Normal   Pulled      Container image "images.canfar.net/skaha/terminal:1.1.1" already present on machine                  2025-05-27T22:02:08Z   2025-05-27T22:02:08Z
Normal   Created     Created container backup-original-passwd-groups                                                      2025-05-27T22:02:08Z   2025-05-27T22:02:08Z
Normal   Started     Started container backup-original-passwd-groups                                                      2025-05-27T22:02:10Z   2025-05-27T22:02:10Z
Normal   Pulled      Container image "redis:7.4.2-alpine3.21" already present on machine                                  2025-05-27T22:02:11Z   2025-05-27T22:02:11Z
Normal   Created     Created container init-users-groups                                                                  2025-05-27T22:02:11Z   2025-05-27T22:02:11Z
Normal   Started     Started container init-users-groups                                                                  2025-05-27T22:02:12Z   2025-05-27T22:02:12Z
Normal   Pulled      Container image "images.canfar.net/skaha/terminal:1.1.1" already present on machine                  2025-05-27T22:02:14Z   2025-05-27T22:02:14Z
Normal   Created     Created container skaha-headless-user-gvfusmzo                                                      2025-05-27T22:02:14Z   2025-05-27T22:02:14Z
Normal   Started     Started container skaha-headless-user-gvfusmzo
```

## Getting Session Logs

To get the logs of a session, you can use the `logs` method. The response will be a dictionary with the session IDs as keys and the logs as values.
The logs are plain text format and can be printed to the console.

```python title="Get session logs"
session.logs(session_ids)
```

## Destroying a Session

When you are done with your session, you can destroy it using the `destroy` method.
The response will be a dictionary with the session IDs as keys and a boolean value indicating whether the session was destroyed or not.

```python title="Destroy a session"
session.destroy(session_ids)
```

```python
{"mrjdtbn9": True, "ov6doae7": True, "ayv4553m": True}
```
