# CLI extensions

!!! note "Unreleased feature"

    Extension discovery is new after v1.5.2. Use a development installation
    containing this change. The v1.5.2 release does not discover plugins.

Installed packages can add root commands through the `canfar.commands`
entry-point group. Root help lists them under **Extensions**, using the
package's Summary metadata or `Installed extension.` when it has no summary.
Built-in command names remain reserved.

## Install and use an extension

Install the extension in the same Python environment as CANFAR. A package
installed in another virtual environment or as a separate uv tool cannot add
commands to this installation.

For example, [canfar-lab](https://github.com/astroai/canfar-lab) contributes
the `lab` command. From a development checkout, preview it without changing
the project's dependencies:

```bash
uv run --with canfar-lab python -m canfar.cli.main --help
uv run --with canfar-lab python -m canfar.cli.main lab --help
```

These commands run this checkout with the extension available to the same
Python interpreter. For a persistent installation, add the extension to the
environment where you installed CANFAR.

Root help and top-level shell completion read package metadata without
importing plugin code. Invoking an extension or completing arguments inside
it loads its Typer application and dependencies. A missing dependency can
therefore fail that extension without breaking root help or completion.

Each extension defines its own options and output. Read its help and package
documentation before using it in a script. CANFAR's built-in `-o/--output`
contract does not apply automatically to extensions.

## Publish an extension

Expose a [Typer](https://typer.tiangolo.com/) application through your
package's entry points:

```toml
[project.entry-points."canfar.commands"]
lab = "canfar_lab.cli.main:lab_app"
```

The name becomes the root command. The target must resolve to a Typer
application, not a function that calls one. Standard entry-point syntax
supports dotted attributes such as `my_package.cli:commands.app`. Existing
extras syntax is accepted, but the loader does not install dependencies.

Choose a unique command name. CANFAR ignores entry points that collide with
built-ins; if installed plugins share a name, the first one discovered wins.
