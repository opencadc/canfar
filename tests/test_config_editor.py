"""Tests for the bound persisted Configuration editor."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from canfar.models.config import Configuration

if TYPE_CHECKING:
    from pathlib import Path


def test_configuration_exposes_only_data_and_editor_for_editing(
    tmp_path: Path,
) -> None:
    """Legacy service operations are not part of the persisted data model."""
    config_path = tmp_path / "config.yaml"
    removed = (
        "save",
        "get_value",
        "set_value",
        "get_credential",
        "storage_identifiers",
        "_resolve_storage",
        "upsert_credential",
        "update_credential",
        "set_active_authentication",
        "remove_authentication",
        "purge_authentication",
        "get_server_by_uri",
        "get_active_server",
        "get_server_for_idp",
        "get_remembered_server_for_idp",
        "set_active_selection",
        "upsert_server",
        "upsert_servers",
    )

    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()

    assert all(not hasattr(config, name) for name in removed)
    assert hasattr(config, "editor")


def test_editor_reads_scalars_mappings_and_whole_lists(tmp_path: Path) -> None:
    """The editor resolves dotted paths without exposing list indexing."""
    config_path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()

        assert config.editor.get("console.width") == 120
        server = config.editor.get("servers.canfar")
        assert server["name"] == "canfar"
        assert config.editor.get("servers.canfar.auths") == ["x509"]

    assert "editor" not in config.model_dump(mode="python")


def test_editor_set_mutates_validated_configuration(tmp_path: Path) -> None:
    """Setting a dotted path updates the bound Configuration in memory."""
    config_path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()

        assert config.editor.set("console.width", 132) is config
        assert config.console.width == 132
        config.editor.set("servers.canfar.auths", ["x509", "oidc"])

        assert config.editor.get("console.width") == 132
        assert config.editor.get("servers.canfar.auths") == ["x509", "oidc"]


def test_editor_replaces_top_level_mapping_without_reloading_saved_state(
    tmp_path: Path,
) -> None:
    """Top-level mapping edits remove records instead of resurrecting YAML keys."""
    config_path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()
        config.editor.set("authentication.srcnet", config.authentication["cadc"])
        config.editor.save()
        config.editor.set("authentication", {"cadc": config.authentication["cadc"]})

    assert set(config.authentication) == {"cadc"}


def test_editor_rejects_list_indexing(tmp_path: Path) -> None:
    """Dotted paths may retrieve a whole list but cannot address its items."""
    config_path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()

        with pytest.raises(ValueError, match="List indices are not supported"):
            config.editor.get("servers.canfar.auths.0")
        with pytest.raises(ValueError, match="List indices are not supported"):
            config.editor.set("servers.canfar.auths.0", "oidc")


def test_editor_save_persists_bound_configuration(tmp_path: Path) -> None:
    """Editor save writes its validated in-memory state to the config file."""
    config_path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()
        config.editor.set("console.width", 133)
        config.editor.save()
        loaded = Configuration()

    assert loaded.console.width == 133


def test_editor_failed_set_preserves_configuration(tmp_path: Path) -> None:
    """Invalid editor updates do not partially mutate the bound config."""
    config_path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()
        original = config.model_dump(mode="python")

        with pytest.raises(ValidationError):
            config.editor.set("console.width", "not-an-int")

    assert config.model_dump(mode="python") == original


def test_editor_save_failure_preserves_existing_file(tmp_path: Path) -> None:
    """A failed editor save leaves the existing YAML untouched."""
    config_path = tmp_path / "config.yaml"
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        config = Configuration()
        config.editor.save()
        original = config_path.read_bytes()
        config.editor.set("console.width", 134)

        with (
            patch("canfar.config.editor.os.fsync", side_effect=OSError("disk full")),
            pytest.raises(OSError, match="Failed to save configuration"),
        ):
            config.editor.save()

    assert config_path.read_bytes() == original
    assert list(tmp_path.iterdir()) == [config_path]
