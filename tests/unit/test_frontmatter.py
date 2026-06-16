import re

from tests.skill import discover_skills


class TestFrontmatter:
    def setup_method(self):
        self.skills = discover_skills()

    def test_required_fields_present(self):
        for skill in self.skills:
            assert skill.metadata.name
            assert skill.metadata.description

    def test_name_matches_directory(self):
        for skill in self.skills:
            assert skill.metadata.name == skill.path.parent.name

    def test_name_is_kebab_case(self):
        for skill in self.skills:
            assert re.search(r"^[a-z][a-z0-9-]*$", skill.metadata.name)

    def test_description_is_meaningful(self):
        for skill in self.skills:
            assert len(skill.metadata.description) > 20
