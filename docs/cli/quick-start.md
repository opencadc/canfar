# CLI Quickstart

Create a notebook Session from a terminal, open it, inspect it, and clean it up.

## 1. Install

```bash
pip install canfar --upgrade
```

## 2. Log in

```bash
canfar login cadc
```

Use SRCNet when that is your IDP:

```bash
canfar login srcnet
```

Check the active Authentication and available Servers:

```bash
canfar auth show
canfar server ls
```

## 3. Work with data

The standard installation includes data commands. Use a configured Storage Name
or the reserved `local` name with an absolute path:

```bash
canfar data ls -lh canSRC:/
canfar data cp local:/absolute/path/file.fits canSRC:/folder/file.fits
```

Cross-source `mv` is unsupported. Copy the file, verify the destination, and
then remove the source with a separate command:

```bash
canfar data cp canSRC:/folder/file.fits other:/folder/file.fits
canfar data ls -lh other:/folder/file.fits
canfar data rm canSRC:/folder/file.fits
```

## 4. Create a notebook

```bash
canfar create notebook skaha/astroml:latest
```

The image shorthand `skaha/astroml:latest` resolves to the CANFAR image
registry. Use the full image name when you want to be explicit:

```bash
canfar create notebook images.canfar.net/skaha/astroml:latest
```

## 5. Check status

```bash
canfar ps
canfar info $(canfar ps -q)
```

Use machine output in scripts:

```bash
canfar ps --json
```

## 6. Open the notebook

```bash
canfar open $(canfar ps -q)
```

Notebook Sessions usually take 60-120 seconds to become reachable.

## 7. Inspect startup events

```bash
canfar events $(canfar ps -q)
canfar logs $(canfar ps -q)
```

## 8. Clean up

```bash
canfar delete $(canfar ps -q)
```

Skip the confirmation prompt when you are scripting:

```bash
canfar delete $(canfar ps -q) --force
```

## Fixed resources

Omit resources for flexible allocation. Set `--cpu`, `--memory`, or `--gpu`
when you need fixed resources.

```bash
canfar create notebook skaha/astroml:latest --cpu 4 --memory 16
```

## Headless job

Use `--` before the command that should run inside the container.

```bash
canfar create headless skaha/terminal:1.1.2 -- python /arc/projects/demo/run.py
```

## Troubleshooting

| Symptom | Command |
| --- | --- |
| Need fresh credentials | `canfar --log-level debug login cadc --force` |
| Need another Server | `canfar server ls` then `canfar server use <name-or-uri>` |
| Session is pending | `canfar events $(canfar ps -q)` |
| Need cluster capacity | `canfar stats` |
| Need structured output | `canfar ps --json` |

Logging controls belong before the command. See
[Logging and observability](logging.md) for the complete policy.
