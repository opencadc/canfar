from pathlib import Path

ALMA_GUIDE = (
    Path(__file__).parents[1] / "docs" / "platform" / "community" / "alma" / "index.md"
)
ALMA_DOCS = ALMA_GUIDE.parent


def test_alma_guide_is_a_text_first_workflow() -> None:
    text = ALMA_GUIDE.read_text()

    for heading in (
        "## Prerequisites",
        "## Workflow",
        "## Expected results",
        "## Troubleshooting",
    ):
        assert heading in text

    assert "canfar login cadc" in text
    assert "canfar create" in text
    assert "canfar data cp" in text
    assert all("![" not in page.read_text() for page in ALMA_DOCS.rglob("*.md"))
