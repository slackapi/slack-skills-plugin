import dataclasses
from collections.abc import Iterator
from pathlib import Path

import markdown
import yaml

from tests.config import SKILLS_ROOT


@dataclasses.dataclass
class Frontmatter:
    #: The skill name extracted from the frontmatter `name` field.
    name: str

    #: The skill description extracted from the frontmatter
    #: `description` field.
    description: str

    #: Optional argument hint from frontmatter `argument-hint` field.
    argument_hint: str | None = None


@dataclasses.dataclass
class Skill:
    #: Parsed frontmatter fields.
    frontmatter: Frontmatter

    #: The markdown content below the frontmatter delimiters.
    body: str

    #: The filesystem path to the source SKILL.md file.
    path: Path

    #: The raw, unprocessed file content including frontmatter.
    content: str

    @classmethod
    def from_path(cls, path: Path) -> Skill:
        content = path.read_text()
        frontmatter: dict[str, str] = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
        return cls(
            frontmatter=Frontmatter(
                name=frontmatter.get("name", ""),
                description=frontmatter.get("description", ""),
                argument_hint=frontmatter.get("argument-hint"),
            ),
            body=body,
            path=path,
            content=content,
        )


def discover_skills() -> tuple[Skill, ...]:
    skills = []
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            skills.append(Skill.from_path(skill_file))
    return tuple(skills)


def load_skill(skill_name: str) -> Skill:
    skill_path = SKILLS_ROOT / skill_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_path}")
    return Skill.from_path(skill_path)


def headings(body: str) -> list[tuple[int, str]]:
    """Return (level, text) for each heading, ignoring ``#`` lines inside code fences.

    Uses Python-Markdown's ``toc`` extension which only considers actual ATX
    headings outside of fenced code blocks.
    """
    md = markdown.Markdown(extensions=["fenced_code", "toc"])
    md.convert(body)

    def _flatten(tokens: list[dict]) -> Iterator[tuple[int, str]]:
        for tok in tokens:
            yield (tok["level"], tok["name"])
            yield from _flatten(tok.get("children", []))

    # `toc_tokens` is added to the Markdown instance at runtime by the `toc`
    # extension, so it isn't present in the type stubs.
    return list(_flatten(md.toc_tokens))  # type: ignore[attr-defined]
