# Slack Plugin

This plugin integrates Slack with Ai tools, providing tools to search, read, and send messages in Slack. It also offers useful skills for users and developers.

## Commands

- `/slack:summarize-channel <channel-name>` — Summarize recent activity in a Slack channel
- `/slack:find-discussions <topic>` — Find discussions about a specific topic across Slack channels
- `/slack:draft-announcement <topic>` — Draft a well-formatted Slack announcement and save it as a draft
- `/slack:standup` — Generate a standup update based on your recent Slack activity
- `/slack:channel-digest <channel1, channel2, ...>` — Get a digest of recent activity across multiple Slack channels

## Development Commands

Requires Python 3.14+. Run `make install` before first use to set up the virtual environment and test dependencies.

**Always use the `make` targets — never invoke `python`, `pytest`, or `ruff` directly.** The targets manage the virtualenv and load `.env` for you; running the underlying tools by hand skips that setup and will behave differently. If a `make` command is broken or missing something you need, fix the `Makefile` rather than working around it with the raw command.

| Command | Purpose |
|---------|---------|
| `make install` | Full setup: venv + deps |
| `make lint` | Ruff linter (line-length=120) |
| `make format` | Ruff auto-format + fix |
| `make test-unit` | Fast validation tests (pytest) |
| `make test-eval` | LLM-judged tests (runs DeepEval against Gemini) |
| `make test` | Both unit + eval tests |
| `make clean` | Remove .venv |
| `make cursor-install` | Install this plugin into a local Cursor for development |
| `make cursor-uninstall` | Uninstall this plugin from the local Cursor install |

The LLM tests read `GEMINI_API_KEY` (required — the eval suite fails when it's unset) and `SLACK_MCP_TOKEN` (a Slack MCP bearer token; the MCP tool-selection test is skipped when it's unset). The DeepEval judge model defaults to `gemini-3.1-flash-lite`, overridable via `GEMINI_MODEL_NAME`. Copy `.env.example` to `.env` and fill in values — the `Makefile` auto-loads `.env` — or pass them inline, e.g. `GEMINI_MODEL_NAME=<model> make test-eval`.

## Cross-Skill References

When one `SKILL.md` references another skill (e.g., to delegate a step instead of duplicating content), follow these rules:

- Use the backticked `plugin:skill` form, e.g. `` `slack:slack-cli` ``.
- When pointing at a specific step, include the step's heading text, not just the number — references survive future reordering.
- Add a sentence of prose explaining what the referenced section does and why you're delegating to it.
- Don't use markdown anchor links (`[text](#step-1)`), `@`-include syntax (`@path/to/SKILL.md`), or bare file paths — none are idiomatic in installed skills, and `@`-includes force-load context.

See `skills/create-slack-app/SKILL.md` Step 1a for an example.

## Testing

Two test layers validate skills:

1. **Unit** (`tests/unit/`) — validates frontmatter fields, naming, and markdown structure. Fast, runs in CI on every PR.
2. **Eval** (`tests/eval/`) — uses DeepEval's `ToolCorrectnessMetric` (threshold 0.8) with a Gemini model to judge whether a skill produces useful output for a sample prompt. Local-only, not in CI.

To add an LLM test for a new skill, create `tests/eval/skills/test_<skill_name>.py` following the pattern in `test_block_kit.py`: define a `PROMPT`, load the skill with `load_skill()`, and assert with `ToolCorrectnessMetric`.

## CI

GitHub Actions (`.github/workflows/ci-build.yml`) gates every PR with:

- **Lint** — `make lint` (Ruff)
- **Test** — `make test-unit` (pytest)

LLM-judged tests are not run in CI (they require a `GEMINI_API_KEY`).
