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

**Always use the `make` targets — never invoke `python`, `pytest`, or `ruff` directly.** The targets manage the virtualenv for you; running the underlying tools by hand skips that setup and will behave differently. (The test suite loads `.env` itself, so env vars are available either way — see below.) If a `make` command is broken or missing something you need, fix the `Makefile` rather than working around it with the raw command.

| Command | Purpose |
|---------|---------|
| `make install` | Full setup: venv + deps |
| `make lint` | Ruff (Python) + rumdl (Markdown) linter checks |
| `make format` | Auto-format: Ruff for Python, rumdl --fix for Markdown |
| `make typecheck` | Mypy static type checks |
| `make test-unit` | Fast validation tests (pytest) |
| `make test-eval` | LLM-judged tests (runs DeepEval against Gemini) |
| `make test` | Both unit + eval tests |
| `make clean` | Remove .venv |
| `make cursor-install` | Install this plugin into a local Cursor for development |
| `make cursor-uninstall` | Uninstall this plugin from the local Cursor install |

The LLM tests read at least one Gemini API key (required — the eval suite fails when none is set) and `SLACK_MCP_TOKEN` (a Slack MCP bearer token; the MCP tool-selection test is skipped when it's unset). To spread requests across the free-tier quota and avoid `RESOURCE_EXHAUSTED`, any env var whose name starts with `GEMINI_API_KEY` (e.g. `GEMINI_API_KEY`, `GEMINI_API_KEY_BOB`) contributes a key to a pool (blank values are skipped), and each eval request picks one at random. The DeepEval judge model defaults to `gemini-3.1-flash-lite`, overridable via `GEMINI_MODEL_NAME`. Copy `.env.example` to `.env` and fill in values — the test suite loads `.env` from the repo root via `python-dotenv` (`tests/config.py`), so values load the same however tests are launched. Real environment variables take precedence over `.env`, so you can also override inline, e.g. `GEMINI_MODEL_NAME=<model> make test-eval`.

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
2. **Eval** (`tests/eval/`) — LLM-judged tests that use a Gemini model. `tests/eval/test_tool_selection.py` asks the model to pick the expected tool/skill for each of a set of prompts. Because Gemini's free tier caps at 15 requests/minute, the test sleeps ~5s between scenarios (see its `teardown_method`) to stay under the limit.

To add an eval scenario, append a `Scenario` (prompt + expected tool) to `SCENARIOS` in `tests/eval/test_tool_selection.py`.

## CI

GitHub Actions (`.github/workflows/ci-build.yml`) gates every PR with:

- **Lint** — `make lint` (Ruff)
- **Typecheck** — `make typecheck` (mypy)
- **Test** — `make test-unit` (pytest)
- **Eval** — `make test-eval` (DeepEval + Gemini)

The eval job reads the `GEMINI_API_KEY_*` (e.g. `GEMINI_API_KEY_BOB`, `GEMINI_API_KEY_MIC`) and `SLACK_MCP_TOKEN` repository secrets; it skips on PRs from forks, which don't receive secrets. The workflow also runs nightly on a schedule, and a `notifications` job posts to Slack (via `SLACK_REGRESSION_FAILURES_WEBHOOK_URL`) when a job fails on `main`.

## Releasing

Releases are automated and run in CI — **you never run a release yourself.** Your only release-related task is adding a changeset when a PR makes a user-facing change.

See the [maintainers guide](.github/maintainers_guide.md#-updating-changesets) for the format.

Everything after that is handled by [changesets](https://github.com/changesets/changesets) and `scripts/changeset_version.sh`: merging to `main` opens a "chore: release" PR, and merging that PR publishes the release.
