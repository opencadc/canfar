"""Tests for the image CLI module."""

from unittest.mock import patch

from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()


def test_image_ls_outputs_table_and_passes_filter() -> None:
    """Ensure image ls prints results and passes filter to fetch."""
    with patch("canfar.cli.image.Images.fetch") as fetch:
        fetch.return_value = ["images.canfar.net/skaha/base-notebook:latest"]

        result = runner.invoke(cli, ["image", "ls", "--filter", "notebook"])

    assert result.exit_code == 0
    assert "CANFAR Images" in result.stdout
    assert "images.canfar.net/skaha/base-notebook:latest" in result.stdout
    fetch.assert_called_once_with(kind="notebook")
