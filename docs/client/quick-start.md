# Python Quickstart

Create a notebook Session, open it, and keep your results before cleaning up.
Run these examples on the computer where you installed and authenticated the
client. Each code block can run as a separate script.

!!! note "Choose a compatible client"

    [Install and set up](get-started.md#install) first. These examples describe
    unreleased changes since v1.4.1; use the development installation when
    following this version of the documentation.

Use the same tab throughout: **Sync Python** for a normal script, or
**Async Python** for an application using `async` and `await`.

!!! tip "Running async examples in a notebook"

    Define `main()` without its final `if __name__` block. In the next cell,
    run `await main()` instead of `asyncio.run(main())`.

## 1. Authenticate

```bash title="Terminal on your computer"
canfar login cadc
canfar image ls --kind notebook
```

Choose an image from that listing. Replace the example image below if it is
unavailable on your server. For SRCNet or direct Python login, see
[authentication and server selection](get-started.md#authenticate).

<span id="async-version"></span>

## 2. Create a notebook

=== "Sync Python"

    ```python title="create_notebook.py" hl_lines="1 3"
    from canfar.sessions import Session

    with Session() as session:
        ids = session.create(
            kind="notebook",
            image="images.canfar.net/skaha/astroml:latest",
            name="quickstart-notebook",
            cores=2,
            ram=4,
        )
        print(ids)
    ```

=== "Async Python"

    ```python title="create_notebook.py" hl_lines="3 6"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = await session.create(
                kind="notebook",
                image="images.canfar.net/skaha/astroml:latest",
                name="quickstart-notebook",
                cores=2,
                ram=4,
            )
            print(ids)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

You receive a list of successfully created Session IDs. Copy the ID and replace
`SESSION_ID` in the following examples. If the list is empty, inspect the error
before continuing. Creation does not mean the application is ready.

<span id="3-open-the-notebook"></span>
<span id="4-inspect-events-and-logs"></span>

## 3. Inspect and connect

=== "Sync Python"

    ```python title="open_notebook.py" hl_lines="1 3"
    from canfar.sessions import Session

    with Session() as session:
        ids = ["SESSION_ID"]
        print(session.info(ids))
        session.connect(ids)
    ```

=== "Async Python"

    ```python title="open_notebook.py" hl_lines="3 6"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = ["SESSION_ID"]
            print(await session.info(ids))
            await session.connect(ids)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

`info()` returns a list of dictionaries containing Session details.
`connect()` opens a browser link for a ready Session and returns `None`.
If it is still `Pending`, inspect the events below, then repeat this step when
it reaches `Running`. Run your analysis in the notebook before cleaning up.

## 4. Read events and logs

=== "Sync Python"

    ```python title="inspect_notebook.py" hl_lines="1 3"
    from canfar.sessions import Session

    with Session() as session:
        ids = ["SESSION_ID"]
        print(session.events(ids))
        print(session.logs(ids))
    ```

=== "Async Python"

    ```python title="inspect_notebook.py" hl_lines="3 6"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = ["SESSION_ID"]
            print(await session.events(ids))
            print(await session.logs(ids))

    if __name__ == "__main__":
        asyncio.run(main())
    ```

Events return a list of dictionaries; logs return a dictionary keyed by Session
ID. A failed request may be omitted from these results. With `verbose=True`,
these methods log their output and return `None` instead.

## 5. Clean up

!!! warning "Save your work first"

    Save notebooks and results under `/arc` or another persistent destination.
    Deleting a Session discards `/scratch` and unsaved application state.
    Closing a Python client or browser tab does not delete the remote Session.

Delete only the ID you created:

=== "Sync Python"

    ```python title="delete_notebook.py" hl_lines="1 3"
    from canfar.sessions import Session

    with Session() as session:
        ids = ["SESSION_ID"]
        print(session.destroy(ids))
    ```

=== "Async Python"

    ```python title="delete_notebook.py" hl_lines="3 6"
    import asyncio

    from canfar.sessions import AsyncSession

    async def main() -> None:
        async with AsyncSession() as session:
            ids = ["SESSION_ID"]
            print(await session.destroy(ids))

    if __name__ == "__main__":
        asyncio.run(main())
    ```

Each requested ID maps to `True` or `False`, indicating whether its deletion
request succeeded. Keep failed IDs for investigation.

<span id="troubleshooting"></span>

## Next steps

- [Common examples](examples.md) for filtering, replicas, and private images.
- [Advanced examples](advanced-examples.md) for a complete batch pipeline.
- [Logging](../cli/logging.md) for diagnostics.
