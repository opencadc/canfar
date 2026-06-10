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
canfar create notebook skaha/astroml:latest
canfar open $(canfar ps -q)
```

```python
from canfar.sessions import Session

session = Session()
ids = session.create(
    kind="notebook",
    image="images.canfar.net/skaha/astroml:latest",
)
session.connect(ids)
```

---
<p align="center">
    <img src="https://img.shields.io/badge/read%20the-documentation-brightgreen?style=for-the-badge&logo=materialformkdocs&logoColor=white">
</p>
