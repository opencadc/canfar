# Authlib feasibility for CANFAR OIDC

- **Date:** 2026-07-10
- **Repository snapshot:** `08454ca8` on `feat/vospace`
- **Authlib evaluated:** `v1.7.2`
- **Question:** Can Authlib replace CANFAR's custom OIDC authentication logic?

## Verdict

**Partly, and the partial replacement is worthwhile. A full replacement is not
available.**

Authlib can take over the OAuth token mechanics that CANFAR should not maintain:
token-endpoint client authentication, device-grant token requests, OAuth error
parsing, `expires_in` normalization, refresh-token rotation, sync/async refresh,
bearer injection, and async refresh serialization.

Authlib does **not** provide a complete RFC 8628 client flow or a dynamic-registration
client. CANFAR must still own a small coordinator for discovery, dynamic client
registration, device authorization, RFC 8628 polling timing, CLI presentation, error
translation, and Pydantic/YAML persistence.

The recommended decision is:

1. Run one authenticated SKA IAM compatibility pilot.
2. If it passes, adopt Authlib for token lifecycle behind the existing OIDC boundary.
3. Keep the Authentication domain and CLI experience CANFAR-owned.
4. Do not add an adapter hierarchy or a second model layer.
5. Only switch platform traffic to Authlib's HTTPX subclasses if that second step
   deletes the custom refresh hooks without introducing cross-client state machinery.

This is a dependency worth adding only if it removes substantial custom protocol
code. Adding Authlib merely to wrap the existing `refresh()` functions would not pay
for itself.

## Capability boundary

| Responsibility | Authlib 1.7.2 | CANFAR recommendation |
| --- | --- | --- |
| Fetch the configured discovery URL | Generic HTTPX client does not auto-discover | Keep the HTTP GET |
| Validate OIDC provider metadata | `OpenIDProviderMetadata.validate()` | Adopt, plus verify the returned issuer against the configured issuer |
| Dynamic client registration request | RFC 7591 implementation is authorization-server-side | Keep CANFAR's small POST and registration policy |
| Device authorization request | RFC 8628 implementation is authorization-server-side | Keep a small request function |
| Device token request | Generic `fetch_token()` accepts an arbitrary grant type and parameters | Replace CANFAR's `_poll_token()` request/parsing logic |
| RFC 8628 polling schedule | No device-client poller | Keep a small standards-compliant loop |
| `authorization_pending` / `slow_down` parsing | Returned as `OAuthError.error` values | Use Authlib parsing; translate at the CANFAR boundary |
| Token endpoint client authentication | Built-in `client_secret_basic`, `client_secret_post`, and `none` | Replace hand-built body/Basic combinations |
| Token response and expiry normalization | Full token mapping; `expires_in` becomes `expires_at` | Adopt |
| Refresh and refresh-token rotation | Full refresh response; preserves the old refresh token if the provider omits a new one | Replace custom sync/async refresh HTTP |
| Automatic bearer injection | `OAuth2Client` and `AsyncOAuth2Client` are HTTPX clients | Candidate for the saved-OIDC branch only |
| Concurrent async refresh | `AsyncOAuth2Client` uses an AnyIO lock | Adopt if Authlib owns request-time refresh |
| CANFAR Authentication Records | No knowledge of CANFAR's domain | Keep canonical `OIDCCredential` models |
| Configuration persistence | `update_token` callback only | Keep one CANFAR callback that atomically updates YAML |
| Browser, QR, Rich progress, UserInfo output | Not a device-flow presenter | Keep in the CLI adapter |
| X.509 and runtime credential precedence | Not CANFAR policy | Keep in `HTTPClient` |
| Logging, redaction, and telemetry | Not solved by adopting Authlib | Leave centralized policy to issue #100 |

The important naming trap is Authlib's advertised "RFC 8628 support." Its
[RFC 8628 documentation](https://docs.authlib.org/en/v1.4.1/specs/rfc8628.html)
teaches `DeviceAuthorizationEndpoint` and `DeviceCodeGrant` for Flask/Django
**authorization servers**. The tagged source likewise contains server endpoint and
grant classes under
[`authlib/oauth2/rfc8628`](https://github.com/authlib/authlib/tree/v1.7.2/authlib/oauth2/rfc8628),
not a device-client coordinator. The same distinction applies to Authlib's
[RFC 7591 implementation](https://docs.authlib.org/en/latest/oauth2/specs/rfc7591.html):
it builds a registration endpoint for an authorization server; it does not call a
provider's registration endpoint on behalf of a client.

Authlib's generic HTTP client is still enough for the token exchange. Its
[`fetch_token` implementation](https://github.com/authlib/authlib/blob/v1.7.2/authlib/oauth2/client.py)
accepts an explicit `grant_type` and arbitrary form parameters, so RFC 8628's device
grant and `device_code` work without a dedicated high-level flow.

## What this improves in the current code

### 1. Correct token-endpoint authentication

`canfar/auth/oidc.py:117-126` currently sends `client_id` and `client_secret` in the
form body **and** sends the same credentials through HTTP Basic authentication.
Registration declares `client_secret_basic`, so the secret should not also be placed
in the request body.

Authlib selects the configured token authentication method once:

```python
oauth = AsyncOAuth2Client(
    client_id=client_id,
    client_secret=client_secret,
    token_endpoint=token_endpoint,
    token_endpoint_auth_method="client_secret_basic",
)

token = await oauth.fetch_token(
    grant_type="urn:ietf:params:oauth:grant-type:device_code",
    device_code=device_code,
)
```

The local probe confirmed that this puts the credentials in the Basic header and
omits `client_secret` from the form body.

### 2. Preserve the complete refresh result

`canfar/auth/oidc.py:140-241` duplicates sync and async refresh functions and returns
only a new access token. It discards `expires_in`, a rotated `refresh_token`, scope,
and other returned fields. A provider that invalidates an old refresh token after
rotation can therefore break the next refresh.

Authlib parses the complete token mapping, normalizes expiry, retains the old refresh
token when a response omits it, and passes the complete result to `update_token`.
These behaviors are implemented in the tagged
[HTTPX OAuth client source](https://github.com/authlib/authlib/blob/v1.7.2/authlib/integrations/httpx_client/oauth2_client.py)
and documented in Authlib's
[refresh and auto-update guide](https://docs.authlib.org/en/1.7.1/oauth2/client/http/#refresh-auto-update-token).

One exact-version caution: use an `async def` update callback with
`AsyncOAuth2Client`. The v1.7.2 source awaits the callback, and the local probe
verified that shape.

### 3. Stop treating every OAuth token as an unverified JWT

Initial login and refresh derive expiry with `canfar.utils.jwt.expiry`
(`canfar/auth/oidc.py:484-487`, `canfar/hooks/httpx/auth.py:77-84`). That helper scans
every dot-separated segment and accepts the first JSON object containing `exp`
(`canfar/utils/jwt.py:7-42`); it does not verify a signature and cannot handle opaque
tokens.

Authlib's
[`OAuth2Token`](https://github.com/authlib/authlib/blob/v1.7.2/authlib/oauth2/rfc6749/wrappers.py)
turns the token response's `expires_in` into `expires_at`. Prefer that protocol field.
If SKA IAM ever omits both fields, do not restore unverified JWT decoding: either
validate claims against the issuer's keys or treat expiry as unknown and rely on a
well-defined token-endpoint error path. The authenticated pilot must confirm the real
SKA IAM token response before `canfar/utils/jwt.py` is deleted.

Refresh-token expiry is not a standard Authlib token-lifecycle field. If the provider
uses opaque refresh tokens, CANFAR should let the token endpoint reject an expired
token and translate `invalid_grant`, rather than guessing locally.

### 4. Fix RFC 8628 edge cases while retaining a small poller

Authlib removes the request encoding and error parsing, but CANFAR still needs the
timer. That remaining loop should follow
[RFC 8628 section 3](https://datatracker.ietf.org/doc/html/rfc8628#section-3):

- `verification_uri_complete` is optional; fall back to the required
  `verification_uri` and display the required `user_code`.
- Display `user_code` even when a QR/complete URI is available.
- Default `interval` to five seconds.
- On `authorization_pending`, wait at least the current interval before another
  request.
- On `slow_down`, increase the interval by five seconds for all later requests.
- Back off on connection timeouts and stop at `expires_in`.
- Stop immediately for `access_denied`, `expired_token`, and other terminal errors.

The current implementation requires `verification_uri_complete`
(`canfar/auth/oidc.py:373-377`) and uses a logarithmic/multiplicative `slow_down`
formula (`canfar/auth/oidc.py:321-341`) instead of RFC 8628's fixed five-second
increase.

A sufficient coordinator remains small:

```python
interval = challenge.get("interval", 5)
deadline = time.monotonic() + challenge["expires_in"]

while time.monotonic() < deadline:
    try:
        return await oauth.fetch_token(
            grant_type=DEVICE_GRANT,
            device_code=challenge["device_code"],
        )
    except OAuthError as error:
        if error.error == "authorization_pending":
            await asyncio.sleep(interval)
        elif error.error == "slow_down":
            interval += 5
            await asyncio.sleep(interval)
        else:
            raise translate_oauth_error(error) from error

raise TimeoutError("Device flow timed out")
```

This is intentionally not a framework, protocol class, or separate DTO layer.

### 5. Validate discovery instead of trusting raw JSON

`canfar/auth/oidc.py:34-56` fetches discovery JSON but does not validate it. Authlib's
[`OpenIDProviderMetadata`](https://github.com/authlib/authlib/blob/v1.7.2/authlib/oidc/discovery/models.py)
validates required OIDC metadata and secure endpoint URLs. CANFAR must still fetch
the configured URL and perform the OpenID Discovery issuer-equality check described
by the
[OpenID Connect Discovery specification](https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderConfigurationValidation).

```python
response = await http.get(discovery_url)
response.raise_for_status()
metadata = OpenIDProviderMetadata(response.json())
metadata.validate()

if metadata["issuer"] != expected_issuer:
    raise AuthenticationError("OIDC discovery issuer mismatch")
```

The issuer comparison should be exact, as required by OpenID Connect Discovery. Keep
the expected issuer as explicit IDP metadata; do not derive it differently at each
call site.

## Recommended integration shape

### First slice: lowest-risk protocol replacement

Keep ordinary `httpx.Client` / `httpx.AsyncClient` for CANFAR platform requests.
Inside the OIDC boundary:

1. Keep the discovery GET, dynamic registration POST, and device-authorization POST.
2. Validate discovery with `OpenIDProviderMetadata` and verify issuer equality.
3. Reuse one `AsyncOAuth2Client` for device token polling.
4. Replace both custom refresh HTTP functions with Authlib and return a complete token
   mapping.
5. Keep the existing CANFAR hook ordering, runtime-credential bypass, headers, and
   canonical `OIDCCredential` persistence while the provider behavior is proven.
6. Move link, `user_code`, browser, QR, and Rich progress rendering into
   `canfar/cli/login_auth.py`.

This slice changes the security-sensitive wire protocol without simultaneously
rewriting X.509/runtime credential selection.

### Optional second slice: delete the OIDC refresh hooks

Authlib's `OAuth2Client` and `AsyncOAuth2Client` subclass HTTPX clients and accept the
timeout, limits, base URL, headers, transport, and event-hook arguments CANFAR already
uses. If the first slice succeeds, use those classes only when the saved credential
mode is OIDC. Then Authlib can own bearer injection and automatic refresh, allowing
the OIDC-specific code in `canfar/hooks/httpx/auth.py` to be deleted.

Do not apply this to runtime tokens, X.509, or default mode. Keep
`X-Skaha-Authentication-Type`, registry headers, error hooks, and CANFAR timeout/pool
policy in `HTTPClient`.

The deletion is conditional on solving one existing state hazard without adding a
new subsystem: `HTTPClient` can cache both a sync and async client, while today a
refresh updates only the client that made the request. A single token-persistence
callback must update the canonical `OIDCCredential` and ensure both cached token
views cannot retain a rotated refresh token. If that requires a shared token manager,
stop after the first slice; the extra abstraction would erase the simplification.

Authlib refreshes 60 seconds before expiry by default. Use `leeway=0` initially if
exact current timing must be preserved, or adopt the default as an explicit behavior
change with tests.

## Concrete persistence example

Operate directly on the domain model; do not round-trip through the legacy `OIDC`
context and do not introduce an Authlib DTO:

```python
async def apply_token(
    config: Configuration, idp: str, token: Mapping[str, Any]
) -> None:
    current = config.get_credential(idp)
    assert isinstance(current, OIDCCredential)
    rotated_refresh = token.get("refresh_token")
    refresh = (
        SecretStr(rotated_refresh) if rotated_refresh else current.token.refresh
    )

    updated = current.model_copy(
        update={
            "token": current.token.model_copy(
                update={
                    "access": SecretStr(token["access_token"]),
                    "refresh": refresh,
                }
            ),
            "expiry": current.expiry.model_copy(
                update={"access": token.get("expires_at")}
            ),
        }
    )
    config.authentication[idp] = updated
    config.save()
```

The real callback must preserve an existing refresh token when the response omits a
new one and translate missing/invalid fields into the established Authentication
error surface.

## Empirical checks performed

### Isolated Authlib 1.7.2 HTTPX probe

An in-memory `httpx.MockTransport` probe verified all of these behaviors against the
released package:

| Check | Result |
| --- | --- |
| Arbitrary RFC 8628 device grant encoded | Pass |
| `device_code` encoded | Pass |
| `authorization_pending` exposed as `OAuthError.error` | Pass |
| `client_secret_basic` used | Pass |
| Client secret omitted from form body | Pass |
| `expires_in` normalized to `expires_at` | Pass |
| Expired token automatically refreshed | Pass |
| Rotated refresh token delivered to async update callback | Pass |
| Refreshed bearer injected into resource request | Pass |

### Live, read-only SKA IAM discovery check

Authlib 1.7.2 `OpenIDProviderMetadata.validate()` passed against the repository's
configured discovery URL on 2026-07-10. The returned metadata advertised:

- issuer `https://ska-iam.stfc.ac.uk/`;
- device authorization, registration, token, and UserInfo endpoints;
- `urn:ietf:params:oauth:grant-type:device_code`; and
- `client_secret_basic`.

Dynamic registration was intentionally not invoked because it creates server-side
state. Device login, UserInfo, refresh rotation, and a CANFAR API request remain the
authenticated integration gate.

### Current-repository baseline

The delegated local audit ran the current Authentication baseline:

```bash
rtk uv run --no-sync pytest \
  tests/test_auth_oidc.py tests/test_hooks_httpx_auth.py \
  tests/test_cli_login_auth.py tests/test_utils_jwt.py \
  -m "not slow" --no-cov -q \
  -o cache_dir=/tmp/canfar-oidc-pytest-cache
# 42 passed

rtk uv run --no-sync pytest \
  tests/test_client.py tests/test_models_auth.py tests/test_models_config.py \
  tests/test_models_config_compat.py tests/test_config.py tests/test_cli_login.py \
  tests/test_cli_config.py tests/test_hooks_httpx_expiry.py \
  -m "not slow" --no-cov -q \
  -o cache_dir=/tmp/canfar-oidc-contract-pytest-cache
# 165 passed
```

No production code or dependency files were changed by this research.

## Dependency assessment

[Authlib v1.7.2](https://github.com/authlib/authlib/releases/tag/v1.7.2) was the
latest release evaluated. Its tagged
[`pyproject.toml`](https://github.com/authlib/authlib/blob/v1.7.2/pyproject.toml)
requires Python 3.10 or newer and uses the BSD-3-Clause license. That matches CANFAR's
Python floor and presents no apparent license conflict with this AGPL project.

CANFAR already depends on HTTPX and already locks `cryptography`. Adding Authlib adds
Authlib itself and `joserfc>=1.6.0` to the lock. This is not a zero-cost dependency,
but it is justified if the migration deletes the duplicate refresh functions, token
request/parser logic, unsafe expiry helper, and eventually the OIDC refresh hooks.

Use the repository's normal lower-bound style if adopted:

```toml
"authlib>=1.7.2",
```

Do not add another OAuth wrapper around Authlib.

## Relationship to planned issue #100

[#100: Logging Architecture and Observability Vertical Slice](https://github.com/opencadc/canfar/issues/100)
is already planned future work. It explicitly owns centralized logging, redaction,
Logfire/OpenTelemetry configuration, and HTTPX instrumentation. This research does
not create a competing logging backlog.

The Authlib work should observe four boundaries:

1. Remove or do not reproduce the raw registration, token, and device-response debug
   logs currently at `canfar/auth/oidc.py:93`, `:128`, and `:371`.
2. Do not build an Authlib-specific redaction or telemetry subsystem; #100 owns the
   centralized policy.
3. Construct Authlib HTTPX clients through the same CANFAR client seam so #100 can
   instrument them without capturing authentication headers or bodies by default.
4. Add one cross-work regression test proving client secrets, device codes, access
   tokens, and refresh tokens do not appear in emitted logs.

Keep the Authlib migration and #100 in separate reviewable changes. They overlap at
HTTPX client construction and should coordinate there, but Authentication behavior
must not be hidden inside the logging work package.

## Adoption gates

Before deleting the current implementation, require:

- a real SKA IAM device login with and without `verification_uri_complete`;
- exact dynamic-registration metadata and authentication-method compatibility;
- `authorization_pending`, `slow_down`, `access_denied`, and `expired_token` tests;
- opaque access and refresh token coverage;
- `expires_in` / `expires_at` and missing-expiry behavior;
- refresh-token rotation and omitted-new-refresh-token behavior;
- sync/async parity or an explicit compatibility decision;
- both cached CANFAR clients observing the same refreshed token state;
- atomic persistence of the complete token result;
- no secret-bearing logs;
- UserInfo and one authenticated CANFAR request; and
- the repository's standard lint, type, non-slow test, and docs gates.

## Primary sources

- [Authlib HTTP clients](https://docs.authlib.org/en/1.7.1/oauth2/client/http/)
- [Authlib HTTPX client guide](https://docs.authlib.org/en/v1.7.0/oauth2/client/http/httpx.html)
- [Authlib v1.7.2 HTTPX OAuth client source](https://github.com/authlib/authlib/blob/v1.7.2/authlib/integrations/httpx_client/oauth2_client.py)
- [Authlib v1.7.2 generic OAuth client source](https://github.com/authlib/authlib/blob/v1.7.2/authlib/oauth2/client.py)
- [Authlib v1.7.2 OIDC metadata validator](https://github.com/authlib/authlib/blob/v1.7.2/authlib/oidc/discovery/models.py)
- [Authlib RFC 8628 server implementation](https://github.com/authlib/authlib/tree/v1.7.2/authlib/oauth2/rfc8628)
- [Authlib RFC 7591 server documentation](https://docs.authlib.org/en/latest/oauth2/specs/rfc7591.html)
- [RFC 8628: OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628)
- [RFC 7591: OAuth 2.0 Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)
- [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html)
- [CANFAR issue #100](https://github.com/opencadc/canfar/issues/100)
