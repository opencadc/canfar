"""Architecture contract for Science Platform Server discovery routes."""

from importlib.util import find_spec
from inspect import iscoroutinefunction, signature

import canfar.models.registry as registry_models
import canfar.server as platform
import canfar.utils.discover as registry_discovery


def test_platform_is_the_only_production_discovery_route() -> None:
    """Discovery enters through Platform and keeps only its low-level adapter."""
    assert callable(platform.discover)
    assert {"fetch", "extract", "check"} <= vars(registry_discovery.Discover).keys()
    assert "max_connections" not in signature(registry_discovery.Discover).parameters
    assert not iscoroutinefunction(registry_discovery.Discover.extract)
    assert "servers" not in vars(registry_discovery.Discover)
    assert not hasattr(registry_discovery, "servers")
    assert not hasattr(registry_models, "ServerResults")
    assert find_spec("canfar.utils.display") is None
