"""Tests for the image CLI module."""

from unittest.mock import patch

from typer.testing import CliRunner

from canfar.cli.main import cli
from canfar.models.containers import Image

runner = CliRunner()


def test_image_ls_outputs_table_and_passes_kind() -> None:
    """Ensure image ls prints results and filters by kind."""
    payload = [
        Image(
            id="images.canfar.net/skaha/base-notebook:latest",
            types=["notebook"],
            digest="sha256:deadbeef",
        )
    ]
    with patch("canfar.cli.image.Images.details") as details:
        details.return_value = payload
        result = runner.invoke(cli, ["image", "ls", "--kind", "notebook"])

    assert result.exit_code == 0
    assert "CANFAR Images" in result.stdout
    assert "skaha/base-notebook:latest" in result.stdout
    details.assert_called_once_with()


def test_image_ls_no_images_message() -> None:
    """Ensure image ls reports when no images are available."""
    with patch("canfar.cli.image.Images.details") as details:
        details.return_value = []

        result = runner.invoke(cli, ["image", "ls"])

    assert result.exit_code == 0
    assert "No images found" in result.stdout


def test_image_ls_rejects_invalid_kind() -> None:
    """Ensure image ls rejects kinds outside the supported list."""
    result = runner.invoke(cli, ["image", "ls", "--kind", "unsupported"])

    assert result.exit_code != 0
    output = result.stdout + result.stderr
    assert "Invalid value for '--kind'" in output


def test_image_ls_outputs_details_table() -> None:
    """Ensure image ls prints server info and detail columns."""
    payload = [
        Image(
            id="images.canfar.net/skaha/terminal:1.1.1",
            types=["headless", "notebook"],
            digest=(
                "sha256:936e8798f9d4f2c6bc2e0fc410711bdf9add23c9cb5b5d515c5aedbf4c235aee"
            ),
        )
    ]

    with patch("canfar.cli.image.Images.details") as details:
        details.return_value = payload
        result = runner.invoke(cli, ["image", "ls"])

    assert result.exit_code == 0
    assert "SERVER=images.canfar.net" in result.stdout
    assert "skaha/terminal:1.1.1" in result.stdout
    assert "936e8798f9d4" in result.stdout
    assert "headless" in result.stdout
    assert "notebook" in result.stdout
    details.assert_called_once_with()


def test_image_ls_filters_by_kind_and_sorts_kinds() -> None:
    """Ensure image ls filters by kind and sorts kind labels."""
    payload = [
        Image(
            id="images.canfar.net/skaha/terminal:1.1.1",
            types=["notebook", "headless"],
            digest="sha256:deadbeef",
        ),
        Image(
            id="images.canfar.net/skaha/other:2.0",
            types=["desktop"],
            digest="sha256:beadfeed",
        ),
    ]

    with patch("canfar.cli.image.Images.details") as details:
        details.return_value = payload
        result = runner.invoke(cli, ["image", "ls", "--kind", "notebook"])

    assert result.exit_code == 0
    assert "skaha/terminal:1.1.1" in result.stdout
    assert "skaha/other:2.0" not in result.stdout
    assert result.stdout.index("notebook") < result.stdout.index("headless")
