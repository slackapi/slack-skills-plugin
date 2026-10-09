import re

from tests.config import AGENT_SETUP_PROMPT, README

# The prompt runs commands from the agent's shell, while the README shows some as
# commands a person types. Each pair maps the prompt's form to the README's. The
# prompt also installs `npx skills` globally (`-g`), which the README documents as
# an option rather than in the command itself.
SHELL_TO_README = (
    ("claude plugin install ", "/plugin install "),
    ("npx -y skills ", "npx skills "),
    (" -g ", " "),
)


def shell_commands(markdown: str) -> list[str]:
    blocks = re.findall(r"```sh\n(.*?)```", markdown, re.DOTALL)
    return [line.strip() for block in blocks for line in block.splitlines() if line.strip()]


class TestAgentSetupPrompt:
    def setup_method(self) -> None:
        self.prompt = AGENT_SETUP_PROMPT.read_text()
        self.readme = README.read_text()

    def test_prompt_has_install_commands(self) -> None:
        assert shell_commands(self.prompt), f"{AGENT_SETUP_PROMPT} has no ```sh install commands"

    def test_install_commands_match_readme(self) -> None:
        for command in shell_commands(self.prompt):
            expected = command
            for shell_form, readme_form in SHELL_TO_README:
                expected = expected.replace(shell_form, readme_form)
            assert expected in self.readme, (
                f"{AGENT_SETUP_PROMPT.name} runs `{command}`, but README.md has no `{expected}`; "
                "update both install sections together"
            )

    def test_prompt_compiles_as_mdx(self) -> None:
        # docs.slack.dev builds with Docusaurus, which compiles this file as MDX.
        # MDX reads `<https://...>` autolinks as JSX tags and fails the build.
        autolinks = re.findall(r"<https?://[^>]*>", self.prompt)
        assert not autolinks, (
            f"{AGENT_SETUP_PROMPT.name} uses `<url>` autolinks {autolinks}, which break the "
            "docs.slack.dev MDX build; write them as `[text](url)` instead"
        )
