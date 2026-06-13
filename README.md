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
canfar ps --json 
# assumes jq is installed
canfar open $(canfar ps --json | jq -r ".[0].id")
```

```python
from canfar.sessions import Session

session = Session()
ids = session.create(
    kind="notebook",
    image="skaha/astroml:26.04",
)
session.connect(ids)
```

---
<p align="center">
    <a href="https://www.opencadc.org/canfar/latest/">
        <img src="https://img.shields.io/badge/read%20the-documentation-brightgreen?style=for-the-badge&logo=materialformkdocs&logoColor=white">
    </a>
</p>
