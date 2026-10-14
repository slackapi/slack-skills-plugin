from pathlib import Path

STANDUP = Path(__file__).parent.parent.parent / "commands" / "standup.md"
PRIVATE_SEARCH = "slack_search_public_and_private"
PUBLIC_SEARCH = "slack_search_public"


class TestStandupCommand:
    def test_searches_private_channels_and_dms(self) -> None:
        text = STANDUP.read_text()
        assert PRIVATE_SEARCH in text
        remainder = text.replace(PRIVATE_SEARCH, "")
        assert PUBLIC_SEARCH not in remainder, (
            "standup must search with slack_search_public_and_private, "
            "which includes DMs and private channels after consent"
        )
