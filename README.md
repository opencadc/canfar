# CANFAR Science Platform

[![Continuous Integration](https://github.com/opencadc/canfar/actions/workflows/ci.yml/badge.svg)](https://github.com/opencadc/canfar/actions/workflows/ci.yml)
[![Continuous Deployment](https://github.com/opencadc/canfar/actions/workflows/cd.yml/badge.svg)](https://github.com/opencadc/canfar/actions/workflows/cd.yml)
[![codecov](https://codecov.io/gh/opencadc/canfar/graph/badge.svg)](https://codecov.io/gh/opencadc/canfar)
[![CodeQL](https://github.com/opencadc/canfar/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/opencadc/canfar/actions/workflows/codeql-analysis.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/opencadc/canfar/badge)](https://scorecard.dev/viewer/?uri=github.com/opencadc/canfar)

## Quickstart

```bash
pip install canfar --upgrade
canfar login cadc
canfar create notebook skaha/astroml:26.04
canfar ps -o json
# assumes jq is installed
SESSION_ID=$(canfar ps -o json | jq -r '.[0].id')
canfar open "$SESSION_ID"
```

```python
from canfar.sessions import Session

with Session() as session:
    ids = session.create(
        name="my-notebook",
        kind="notebook",
        image="skaha/astroml:26.04",
    )
    session.connect(ids)
```

## Agent skills

```bash
npx skills add opencadc/canfar --skill canfar
```

Select the skill in your coding agent, then ask it to start a notebook or help
with another CANFAR task. See [CANFAR Agent Skill](docs/platform/agent-skill.md)
for installation and examples for your agent.

## Community

Ask questions and share ideas in [Discussions](https://github.com/opencadc/canfar/discussions),
or [report a problem](https://github.com/opencadc/canfar/issues/new/choose). Read the [community guidelines](docs/platform/community/guidelines.md) for
the roadmap and follow-up process. Email [support@canfar.net](mailto:support@canfar.net) if you prefer not to create a GitHub account.

---
<p align="center">
    <a href="https://www.opencadc.org/canfar/latest/">
        <img src="https://img.shields.io/badge/read%20the-documentation-brightgreen?style=for-the-badge&logo=materialformkdocs&logoColor=white">
    </a>
</p>
