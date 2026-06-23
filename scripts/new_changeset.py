"""Scaffold a new changeset file so contributors never need Node.js.

Writes ``.changeset/<random-name>.md`` with the frontmatter changesets expects:

    ---
    "slack": <patch|minor|major>
    ---

    <summary>

Runs interactively (prompts for bump level + summary) or non-interactively via
``--bump`` / ``--summary`` flags.
"""

import argparse
import logging
import random
from pathlib import Path

logger = logging.getLogger(Path(__file__).stem)

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGESET_DIR = REPO_ROOT / ".changeset"

PACKAGE_NAME = "slack"
BUMP_LEVELS = ("patch", "minor", "major")

# Used to build memorable, collision-resistant filenames (changesets convention).
ADJECTIVES = (
    "brave", "calm", "clever", "eager", "fancy", "gentle", "happy", "jolly",
    "kind", "lively", "proud", "quick", "shiny", "smart", "swift", "witty",
)
ANIMALS = (
    "otters", "pandas", "foxes", "lions", "tigers", "whales", "eagles",
    "owls", "bears", "wolves", "moose", "hawks", "seals", "rabbits",
)


def random_slug() -> str:
    return f"{random.choice(ADJECTIVES)}-{random.choice(ANIMALS)}-{random.randint(100, 999)}"


def render(bump: str, summary: str) -> str:
    return f'---\n"{PACKAGE_NAME}": {bump}\n---\n\n{summary.strip()}\n'


def prompt_bump() -> str:
    options = ", ".join(BUMP_LEVELS)
    while True:
        choice = input(f"Bump level ({options}) [patch]: ").strip().lower() or "patch"
        if choice in BUMP_LEVELS:
            return choice
        print(f"Please choose one of: {options}")


def write_changeset(bump: str, summary: str, directory: Path = CHANGESET_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{random_slug()}.md"
    path.write_text(render(bump, summary))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="Create a changeset describing a user-facing change.",
    )
    parser.add_argument("--bump", choices=BUMP_LEVELS, help="Semver bump level")
    parser.add_argument("--summary", help="Changelog summary for the change")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    bump = args.bump or prompt_bump()
    summary = args.summary or input("Summary: ").strip()
    if not summary:
        parser.error("a non-empty summary is required")

    path = write_changeset(bump, summary)
    logger.info(f"Created {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
