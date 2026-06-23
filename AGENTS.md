# Slack Plugin

This plugin integrates Slack with Ai tools, providing tools to search, read, and send messages in Slack. It also offers useful skills for users and developers.

## Commands

- `/slack:summarize-channel <channel-name>` — Summarize recent activity in a Slack channel
- `/slack:find-discussions <topic>` — Find discussions about a specific topic across Slack channels
- `/slack:draft-announcement <topic>` — Draft a well-formatted Slack announcement and save it as a draft
- `/slack:standup` — Generate a standup update based on your recent Slack activity
- `/slack:channel-digest <channel1, channel2, ...>` — Get a digest of recent activity across multiple Slack channels

## Development Commands

Requires Python 3.14+. Run `make install` before first use to set up the virtual environment, test dependencies, and local Ollama instance.

**Always use the `make` targets — never invoke `python`, `pytest`, or `ruff` directly.** The targets manage the virtualenv, load `.env`, and start/stop the local Ollama instance for you; running the underlying tools by hand skips that setup and will behave differently. If a `make` command is broken or missing something you need, fix the `Makefile` rather than working around it with the raw command.

| Command | Purpose |
|---------|---------|
| `make install` | Full setup: venv + deps + Ollama + gemma4 model |
| `make lint` | Ruff linter (line-length=120) |
| `make format` | Ruff auto-format + fix |
| `make test-unit` | Fast validation tests (pytest) |
| `make test-eval` | LLM-judged tests (starts Ollama, runs DeepEval, stops Ollama) |
| `make test` | Both unit + eval tests |
| `make clean` | Remove .venv and .ollama |
| `make cursor-install` | Install this plugin into a local Cursor for development |
| `make cursor-uninstall` | Uninstall this plugin from the local Cursor install |
| `make changeset` | Create a changeset for the next release (see Releasing) |

The LLM tests read two environment variables: `OLLAMA_MODEL_NAME` (the DeepEval judge model, defaults to `gemma4`) and `SLACK_MCP_TOKEN` (a Slack MCP bearer token; the MCP tool-selection test is skipped when it's unset). Copy `.env.example` to `.env` and fill in values — the `Makefile` auto-loads `.env` — or pass them inline, e.g. `OLLAMA_MODEL_NAME=<model> make test-eval`.

## Testing

Two test layers validate skills:

1. **Unit** (`tests/unit/`) — validates frontmatter fields, naming, and markdown structure. Fast, runs in CI on every PR.
2. **Eval** (`tests/eval/`) — uses DeepEval's `ToolCorrectnessMetric` (threshold 0.8) with a local Ollama model to judge whether a skill produces useful output for a sample prompt. Local-only, not in CI.

To add an LLM test for a new skill, create `tests/eval/skills/test_<skill_name>.py` following the pattern in `test_block_kit.py`: define a `PROMPT`, load the skill with `load_skill()`, and assert with `ToolCorrectnessMetric`.

## CI

GitHub Actions (`.github/workflows/ci-build.yml`) gates every PR with:

- **Lint** — `make lint` (Ruff)
- **Test** — `make test-unit` (pytest)

LLM-judged tests are not run in CI (Ollama + model download would exceed time budget).

## Releasing

Releases are driven by [changesets](https://github.com/changesets/changesets). The
plugin runtime stays pure Python — Node is only needed for changesets tooling (`make
changeset` locally and the release workflow in CI). A minimal `package.json` (committed at
the repo root) is the version source of truth; `scripts/sync_versions.py` propagates
its version into both `plugin.json` manifests.

**Per change:** every PR with a user-facing change adds a changeset. Run `make changeset`
(or hand-write a `.changeset/<name>.md`); see the
[maintainers guide](.github/maintainers_guide.md#-updating-changesets) for the format and
how to pick a bump level.

**On merge to `main`** (`.github/workflows/release.yml`):

1. If changesets are pending, the `changesets/action` opens/updates a **"chore: release"**
   PR that runs `changeset version` — bumping `package.json`, syncing the version into
   both `plugin.json` manifests (`scripts/sync_versions.py`),
   writing `CHANGELOG.md`, and deleting the consumed changesets.
2. Merging that PR (no changesets left) triggers `changeset publish`, which — because the
   package is `private` — skips npm, creates the `v<version>` git tag, and publishes a
   GitHub release with notes from `CHANGELOG.md`.

A one-time repo setting is required: **Settings → Actions → "Allow GitHub Actions to
create and approve pull requests."**
