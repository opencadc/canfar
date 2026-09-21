--8<-- "CONTRIBUTING.md"
# Contributing

Contributions to CANFAR include code, tests, documentation, examples, issue
reports, and improvements to the user experience. Read the
[Code of Conduct](conduct.md) before participating.

## Set up

CANFAR uses [uv](https://docs.astral.sh/uv/) for development:

```bash
uv sync --all-extras --dev
uv run pre-commit install --hook-type commit-msg
```

Use a valid CANFAR account and certificate only for integration tests. Most
pull-request checks are deterministic:

```bash
uv run --no-sync pytest tests -m "not slow" --no-cov -q -o cache_dir=/tmp/canfar-pytest-cache
uv run --group docs mkdocs build
```

The full test suite contacts the Science Platform and requires valid
credentials. Run it only when those credentials are available.

## Documentation

Keep examples aligned with the installed CLI and Python API. Build the site
locally with `uv run --group docs mkdocs serve` and check navigation, links,
images, and code blocks before opening a pull request.

## Submit a change

Open an issue or pull request on [GitHub](https://github.com/opencadc/canfar).
Use a focused branch and a [Conventional Commit](https://www.conventionalcommits.org/)
message. Include the tests or documentation build you ran in the pull request
description.

The repository's [contributor guide](https://github.com/opencadc/canfar/blob/main/CONTRIBUTING.md)
contains the complete project policy.
