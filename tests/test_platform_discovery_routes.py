"""Architecture contract for Science Platform Server discovery routes."""

from importlib.util import find_spec
from inspect import iscoroutinefunction, signature

import canfar.models.registry as registry_models
import canfar.server as platform
import canfar.utils.discover as registry_discovery


def test_platform_is_the_only_production_discovery_route() -> None:
    """Discovery enters through Platform and keeps only its low-level adapter."""
    assert callable(platform.discover)
    assert iscoroutinefunction(registry_discovery.fetch)
    assert iscoroutinefunction(registry_discovery.check)
    assert not iscoroutinefunction(registry_discovery.extract)
    assert "max_connections" not in signature(registry_discovery.client).parameters
    assert not hasattr(registry_discovery, "servers")
    assert not hasattr(registry_models, "ServerResults")
    assert find_spec("canfar.utils.display") is None
