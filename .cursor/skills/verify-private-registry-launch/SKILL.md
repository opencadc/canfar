---
name: verify-private-registry-launch
description: "Prove a private Session launch sends the saved registry credential for the image host, else CANFAR_REGISTRY__USERNAME and CANFAR_REGISTRY__SECRET, and otherwise raises before any POST. Use when changing registry_headers, registry_credential, env_credential, or Session.create private handling."
---

# Verify private registry launch

**Property.** A private `Session.create` sends the saved credential for the image host, or `CANFAR_REGISTRY__USERNAME` and `CANFAR_REGISTRY__SECRET` when that host has nothing saved, and otherwise raises `RegistryCredentialsRequired` before any request. A public launch sends no `X-Skaha-Registry-Auth` header.

**Harm.** A private image is submitted with no credential or the wrong secret, or an environment secret is written into the configuration file.

## Tool

Pytest enumeration of the real `Session.create` path in `tests/test_private_registry_launch.py`. This repo has no Python code verifier. The decision is a small lattice, so calling the code is cheaper and closer to the code than a TLA+ model of the same steps. A model could pass while `registry_headers` drifted.

## Run

From the canfar repository root:

```bash
UV_CACHE_DIR=/tmp/canfar-uv-cache rtk proxy uv run --no-sync pytest tests/test_private_registry_launch.py --no-cov -q -n0 -o cache_dir=/tmp/canfar-pytest-cache
```

Exit 0 means every combination held. A failure names the case (`private`, `host`, `saved`, `env`, `url`) and the step that broke. Read it as: build the image `HOST/proj/img:1` → `Session.create(..., errors="ignore")` → one POST carries the winning header, or `RegistryCredentialsRequired` and no request.

## Coverage

- Files: `canfar/helpers/session.py` (`registry_headers`), `canfar/models/config.py` (`Configuration.registry_credential`), `canfar/models/registry.py` (`env_credential`, `_env_value`), `canfar/sessions.py` (`Session.create`), `canfar/exceptions/session.py` (`RegistryCredentialsRequired`).
- `AsyncSession.create` calls the same `registry_headers` before its posts and is not enumerated separately.
- `canfar create --private` and `--dry-run` call `registry_headers` from `_require_registry_credential` in `canfar/cli/create.py` and are not enumerated separately.
- Sync commit: `8e20d275`. Move this forward only after the check exits 0 and you have confirmed the test still describes those functions at the new commit.

## Bounds

- Hosts: `images.canfar.net` and `harbor.example`. Every subset may be saved.
- Environment: absent, username only, secret only, both at canonical case, both at lower case.
- `CANFAR_REGISTRY__URL` is either absent or `https://images.canfar.net/v2`. It must not change the result.
- One replica, `errors="ignore"`, secrets `saved-ada`, `saved-bob`, and `env-s3cret`. 160 combinations.
- Does not contact a registry. Does not check that Skaha accepts the header. Does not check `canfar registry login` or file mode `0600`.

## Able to fail

Do not leave these edits in the tree. Each one must fail the command above.

1. In `registry_headers`, return `{}` instead of raising `RegistryCredentialsRequired`. Missing-credential cases send a POST.
2. In `registry_credential`, return `env_credential()` before the saved lookup. A saved host sends the environment secret.
3. In `registry_credential`, return `None` when nothing is saved. Environment cases raise instead of sending the environment header.
4. In `registry_headers`, drop `if not request.private: return {}`. A public launch sends a header or raises.
5. In `registry_credential`, store the environment credential on `self.registries` before returning it. The environment secret is kept on the configuration.

## Before commit

From the canfar repository root, before any `git commit`:

```bash
UV_CACHE_DIR=/tmp/canfar-uv-cache rtk proxy uv run --no-sync pre-commit run --all-files
UV_CACHE_DIR=/tmp/canfar-uv-cache rtk proxy uv run --no-sync pytest tests -m "not slow" --no-cov -q -o cache_dir=/tmp/canfar-pytest-cache
```

Both must exit 0. Do not commit with a failing or skipped pre-commit run, and do not pass `--no-verify`.

## Maintain

When covered code changes after the sync commit, re-run this check before treating the launch decision as done. `/maintain-formal-verification-skill` brings the record back in line.
