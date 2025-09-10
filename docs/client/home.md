# CANFAR Clients

A powerful Python API and CLI for the CANFAR Science Platform.

=== ":fontawesome-solid-wand-magic-sparkles: Client"

    !!! example ":material-language-python: API"

        === "`sync`"

            ```python
            from canfar.sessions import Session

            session = Session()
            ids = session.create(
                name="test",
                image="images.canfar.net/skaha/astroml:latest",
                kind="headless",
                cmd="env",
                env={"KEY": "VALUE"},
                replicas=3,
            )
            print(ids)
            ```

        === "`async`"

            ```python
            from canfar.sessions import AsyncSession
            
            session = AsyncSession()
            ids = await session.create(
                name="test",
                image="images.canfar.net/skaha/astroml:latest",
                kind="headless",
                cmd="env",
                env={"KEY": "VALUE"},
                replicas=3,
            )
            print(ids)
            ```
        
        === "`async context`"

            ```python
            from canfar.sessions import AsyncSession
            
            async with AsyncSession() as session:
                ids = await session.create(
                    name="test",
                    image="images.canfar.net/skaha/astroml:latest",
                    kind="headless",
                    cmd="env",
                    env={"KEY": "VALUE"},
                    replicas=3,
                )
                print(ids)
            ```

    !!! example ":simple-gnubash: CLI"

        ```bash title="Create a Session"
        canfar launch headless --env KEY=VALUE --replicas 3 images.canfar.net/skaha/astroml:latest 
        ```

=== ":material-download: Download"

    !!! info "Installation"

        ```bash title="Install from PyPI"
        pip install canfar
        ```

        ```bash title="Add as Dependency"
        uv add canfar
        ```

[:simple-python: Python Client](quick-start.md){: .md-button .md-button--primary }
[:simple-gnubash: Explore the CLI](../cli/quick-start.md){: .md-button .md-button--primary }
[:fontawesome-brands-github: Codebase](https://github.com/opencadc/canfar){: .md-button .md-button--primary }