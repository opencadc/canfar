"""Contract tests for supported model type aliases."""

from typing import get_args

from canfar.models.types import Kind, Pruneable, Status, View


def test_supported_literal_alias_values() -> None:
    """Supported aliases retain their documented literal values."""
    assert {
        "Kind": get_args(Kind),
        "Pruneable": get_args(Pruneable),
        "Status": get_args(Status),
        "View": get_args(View),
    } == {
        "Kind": (
            "desktop",
            "notebook",
            "carta",
            "headless",
            "firefly",
            "desktop-app",
            "contributed",
        ),
        "Pruneable": (
            "desktop",
            "notebook",
            "carta",
            "headless",
            "firefly",
            "contributed",
        ),
        "Status": (
            "Pending",
            "Running",
            "Terminating",
            "Succeeded",
            "Completed",
            "Error",
            "Failed",
        ),
        "View": ("all",),
    }
