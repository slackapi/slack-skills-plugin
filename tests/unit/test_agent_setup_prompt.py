import re

from tests.config import AGENT_SETUP_PROMPT, README, SKILLS_ROOT

# The prompt runs commands from the agent's shell, while the README shows some as
# commands a person types. Each pair maps the prompt's form to the README's. The
# prompt also installs `npx skills` globally (`-g`), which the README documents as
# an option rather than in the command itself.
SHELL_TO_README = (
    ("claude plugin install ", "/plugin install "),
    ("claude plugin marketplace add ", "/plugin marketplace add "),
    ("npx -y skills@latest ", "npx skills "),
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

    def test_prompt_resolves_both_skill_reference_forms(self) -> None:
        # Skills written before the bare-name change say `slack:<name>`, and installed or
        # cached copies keep saying it, so the prompt resolves both forms to a hosted copy.
        for form in ('"the `<name>` skill"', "`slack:<name>`"):
            assert form in self.prompt, (
                f"{AGENT_SETUP_PROMPT.name} does not resolve skill references written as {form}"
            )

    def test_prompt_updates_existing_installs(self) -> None:
        # An older install can lack steps the prompt relies on, like the `--app` path in
        # create-slack-app, so the prompt updates an existing install instead of skipping it.
        for command in ("claude plugin update slack@", "codex plugin marketplace upgrade slack"):
            assert command in self.prompt, (
                f"{AGENT_SETUP_PROMPT.name} does not update an existing install with `{command}`"
            )
        assert "skip to Step 2" not in self.prompt, (
            f"{AGENT_SETUP_PROMPT.name} skips the install when skills are present, leaving an older install"
        )

    def test_prompt_follows_the_hosted_create_slack_app(self) -> None:
        # The hosted skills deploy with the prompt, while a loaded copy can be from an older
        # install, so Step 2 always reads the hosted copy.
        hosted = "https://docs.slack.dev/.well-known/skills/create-slack-app/SKILL.md"
        assert hosted in self.prompt, f"{AGENT_SETUP_PROMPT.name} does not point Step 2 at {hosted}"
        assert "If the skill is loaded" not in self.prompt, (
            f"{AGENT_SETUP_PROMPT.name} prefers a loaded create-slack-app, which can be from an older install"
        )
