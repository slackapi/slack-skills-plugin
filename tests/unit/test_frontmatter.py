import re

from tests.skill import discover_skills


class TestFrontmatter:
    def setup_method(self) -> None:
        self.skills = discover_skills()

    def test_required_fields_present(self) -> None:
        for skill in self.skills:
            assert skill.frontmatter.name
            assert skill.frontmatter.description

    def test_name_matches_directory(self) -> None:
        for skill in self.skills:
            assert skill.frontmatter.name == skill.path.parent.name

    def test_name_is_kebab_case(self) -> None:
        for skill in self.skills:
            assert re.search(r"^[a-z][a-z0-9-]*$", skill.frontmatter.name)

    def test_description_is_meaningful(self) -> None:
        for skill in self.skills:
            assert len(skill.frontmatter.description) > 20
