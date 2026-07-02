from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ERROR_CODE = "mcp_externally_shared_channel_restricted"


def test_readme_documents_slack_connect_send_restriction():
    readme = (ROOT / "README.md").read_text()

    assert ERROR_CODE in readme
    assert "Slack Connect" in readme
    assert "slack_send_message" in readme


def test_slack_messaging_skill_explains_slack_connect_send_error():
    skill = (ROOT / "skills/slack-messaging/SKILL.md").read_text()

    assert ERROR_CODE in skill
    assert "Do not retry" in skill
    assert "preserve the drafted message text" in skill
