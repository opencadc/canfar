# CANFAR Clients

A powerful Python interface and CLI for the CANFAR Science Platform.

=== ":fontawesome-solid-wand-magic-sparkles: Client"

    !!! example ":material-language-python: API"

        ```python title="Create a Session"
        from canfar.sessions import AsyncSession

        with AsyncSession() as session:
            await session.create(
                name="test",
                image="images.canfar.net/skaha/base-notebook:latest",
                kind="headless",
                cmd="env",
                env={"KEY": "VALUE"},
                replicas=3,
            )
        ```

    !!! example ":simple-gnubash: CLI"

        ```bash title="Create a Session"
        canfar create headless --env KEY=VALUE --replicas 3images.canfar.net/skaha/base-notebook:latest 
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