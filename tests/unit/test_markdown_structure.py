import re

from tests.skill import discover_skills


class TestMarkdownStructure:
    def setup_method(self) -> None:
        self.skills = discover_skills()

    def test_has_content(self) -> None:
        for skill in self.skills:
            assert len(skill.body) > 100

    def test_has_top_level_heading(self) -> None:
        for skill in self.skills:
            assert re.search(r"(?m)^#\s+", skill.body)

    def test_has_section_structure(self) -> None:
        for skill in self.skills:
            headings = re.findall(r"^##\s+", skill.body, re.MULTILINE)
            assert len(headings) >= 2
