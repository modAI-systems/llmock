"""Test that the skill reference config.yaml stays in sync with the root config.yaml."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_skill_config_matches_root_config() -> None:
    """The config.yaml shipped in the llmock-skill must be identical to the root one."""
    root_config = ROOT / "config.yaml"
    skill_config = ROOT / "docs" / "llmock-skill" / "references" / "config.yaml"

    assert root_config.exists(), f"Root config not found: {root_config}"
    assert skill_config.exists(), f"Skill config not found: {skill_config}"

    root_text = root_config.read_text()
    skill_text = skill_config.read_text()

    assert root_text == skill_text, (
        "docs/llmock-skill/references/config.yaml has diverged from the root config.yaml. "
        "Copy the root config.yaml to docs/llmock-skill/references/config.yaml to fix this."
    )
