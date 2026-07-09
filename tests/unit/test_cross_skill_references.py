import re

from tests.config import PLUGIN_NAME
from tests.skill import discover_skills


class TestCrossSkillReferences:
    def setup_method(self) -> None:
        self.skills = discover_skills()
        self.skill_names = {skill.frontmatter.name for skill in self.skills}

    def test_plugin_skill_references_target_real_skills(self) -> None:
        pattern = re.compile(rf"`{re.escape(PLUGIN_NAME)}:([a-z0-9-]+)`")
        for skill in self.skills:
            for target in pattern.findall(skill.body):
                assert target in self.skill_names, f"{skill.path} references unknown skill `{PLUGIN_NAME}:{target}`"

    def test_no_markdown_anchor_links(self) -> None:
        for skill in self.skills:
            # .find() returns -1 if the substring is not found
            anchor_index = skill.body.find("](#")

            snippet = skill.body[anchor_index : anchor_index + 30]
            assert anchor_index == -1, (
                f"'{skill.path}' uses a markdown anchor link near "
                f'"{snippet}"; '
                "cross-skill references must not use `[text](#anchor)` links"
            )

    def test_no_bare_skill_file_paths(self) -> None:
        for skill in self.skills:
            # .find() returns -1 if the substring is not found
            path_index = skill.body.find("SKILL.md")

            # A bare path precedes "SKILL.md" (e.g. "skills/foo/SKILL.md"), so
            # the error window reaches back to show that leading context.
            start = max(0, path_index - 30)
            snippet = skill.body[start : path_index + 8]
            assert path_index == -1, (
                f"'{skill.path}' references a SKILL.md path near "
                f'"{snippet}"; '
                "reference skills by the backticked `plugin:skill` form instead"
            )
