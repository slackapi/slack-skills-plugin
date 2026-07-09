from tests.config import get_gemini_api_key_pool


class TestGeminiApiKeyPool:
    def test_collects_all_prefixed_vars(self) -> None:
        environ = {"GEMINI_API_KEY": "primary", "GEMINI_API_KEY_BOB": "bob"}
        assert set(get_gemini_api_key_pool(environ)) == {"primary", "bob"}

    def test_bare_prefix_included(self) -> None:
        assert get_gemini_api_key_pool({"GEMINI_API_KEY": "primary"}) == ["primary"]

    def test_blank_and_whitespace_values_skipped(self) -> None:
        environ = {"GEMINI_API_KEY": "", "GEMINI_API_KEY_X": "   ", "GEMINI_API_KEY_Y": "real"}
        assert get_gemini_api_key_pool(environ) == ["real"]

    def test_values_are_stripped(self) -> None:
        assert get_gemini_api_key_pool({"GEMINI_API_KEY": "  abc  "}) == ["abc"]

    def test_non_matching_vars_ignored(self) -> None:
        environ = {"SLACK_MCP_TOKEN": "token", "PATH": "/usr/bin", "GEMINI_MODEL_NAME": "flash"}
        assert get_gemini_api_key_pool(environ) == []

    def test_prefix_must_be_at_start(self) -> None:
        assert get_gemini_api_key_pool({"MY_GEMINI_API_KEY": "nope"}) == []

    def test_empty_environment(self) -> None:
        assert get_gemini_api_key_pool({}) == []
