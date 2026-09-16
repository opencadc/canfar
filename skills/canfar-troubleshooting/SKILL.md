---
name: canfar-troubleshooting
description: >
  CANFAR troubleshooting: session Pending stuck, home quota full, scratch not
  visible to teammate, files lost after session end, canfar auth failed,
  Jupyter or hub not loading, permission denied, batch job failed. Use when
  something broke or behavior seems wrong on CANFAR.
---
# Troubleshooting

## Diagnostics bundle

The filesystem lines below use CADC paths. On another deployment, substitute
the persistent home/project mount visible inside the Session.

```bash
canfar ps
canfar auth show
canfar server ls
canfar stats
canfar events <session-id>
df -h /arc/home/$USER /scratch 2>/dev/null
du -sh /arc/home/$USER/* 2>/dev/null | sort -h | tail
```

## Symptom → action

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Teammate can't see `/scratch/...` | Scratch is Session-private | Persistent project storage or VOSpace |
| Files gone after Session delete | Never copied to persistent storage | Lost if only on scratch—persist next time |
| Home save/login fails | Home quota full | `df`/`du`; move data to project; `canfar-quotas` |
| **Create rejected** "maximum … sessions" | Interactive session cap hit | `canfar ps`; delete idle sessions |
| New session **Pending** long | Site queue, image pull, or probe | `canfar events <id>`; not always "cap" |
| **Permission denied** on project | Identity, membership, allocation, or POSIX mode | `id`; `ls -ld`; `canfar-groups`/`permissions` |
| `canfar login` fails | Authentication or Server discovery/selection | `canfar-auth`; debug login; `server ls` |
| `vcp` / Vault slow or fails | Large file via web UI | `canfar-transfers`; CLI `vcp` |
| Batch job **Failed** | Bad image, OOM, bad path | Session logs; verify persistent paths; `canfar-batch` |
| Quota % stuck after delete | Ceph `rbytes` lag | Wait; re-check `df` |
| CVMFS empty at `/cvmfs` | Lazy mount or not enabled | `ls /cvmfs/soft.computecanada.ca/` |
| Can't push Harbor image | No registry permission | `canfar-permissions`; project admin |

## Platform vs user error

1. **Scratch invisible to others** — by design, not a bug.
2. **Project dir missing** — allocations are managed; `mkdir` under a site's projects root won't create one.
3. **Archive download fails** — separate from VOSpace; see `canfar-cadc-data`.

## Escalation

Platform outages, persistent cluster-wide Pending:

- CADC: **`support@canfar.net`** · [Discord](https://discord.gg/vcCQ8QBvBa)
- Other deployments: your portal support / operator contact

## Agent rules

1. Confirm the persistence tier before calling it a bug (scratch vs persistent
   POSIX storage vs VOSpace; CADC names these ARC and Vault).
2. Give one concrete command + expected output.
3. Do not advise `sudo` — users lack root in sessions.
