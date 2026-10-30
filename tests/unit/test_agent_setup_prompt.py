import re

from tests.config import AGENT_SETUP_PROMPT, README, SKILLS_ROOT

# The prompt runs commands from the agent's shell, while the README shows some as
# commands a person types. Each pair maps the prompt's form to the README's. The
# prompt also installs `npx skills` globally (`-g`), which the README documents as
# an option rather than in the command itself.
SHELL_TO_README = (
    ("claude plugin install ", "/plugin install "),
    ("npx -y skills ", "npx skills "),
    (" -g ", " "),
)


# App Settings ends the prompt it shows with these arguments after a developer creates an
# app there, and names its template without a language. Renaming an argument or dropping a
# name from the prompt's table breaks every prompt developers have already copied.
APP_SETTINGS_ARGUMENTS = ("--app", "--template", "--team")
APP_SETTINGS_TEMPLATES = (
    "bolt-starter-template",
    "bolt-starter-agent",
    "bolt-support-agent",
    "bolt-custom-step-template",
    "bolt-blank-template",
)
CREATE_SLACK_APP = SKILLS_ROOT / "create-slack-app" / "SKILL.md"


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

    def test_prompt_and_skill_take_app_settings_arguments(self) -> None:
        skill = CREATE_SLACK_APP.read_text()
        for argument in APP_SETTINGS_ARGUMENTS:
            assert f"`{argument}`" in self.prompt, (
                f"{AGENT_SETUP_PROMPT.name} does not document `{argument}`, which App Settings passes to it"
            )
            assert f"`{argument}`" in skill, (
                f"create-slack-app does not document `{argument}`, which {AGENT_SETUP_PROMPT.name} passes to it"
            )

    def test_prompt_maps_every_app_settings_template(self) -> None:
        for name in APP_SETTINGS_TEMPLATES:
            assert f"| `{name}` |" in self.prompt, (
                f"{AGENT_SETUP_PROMPT.name} has no template table row for `{name}`, which App Settings sends"
            )

    def test_prompt_maps_each_template_to_its_own_repo(self) -> None:
        # Each template name has a repo per language, so a row that maps a name to a
        # different template's repo gives the developer an app they did not choose.
        for name in APP_SETTINGS_TEMPLATES:
            suffix = name.removeprefix("bolt-")
            row = f"| `{name}` | `slack-samples/bolt-js-{suffix}` | `slack-samples/bolt-python-{suffix}` |"
            assert row in self.prompt, (
                f"{AGENT_SETUP_PROMPT.name} does not map `{name}` to the matching JavaScript and "
                f"Python repos; expected the row {row}"
            )
