from tests.config import EXPECTED_SKILLS
from tests.skill import discover_skills


class TestSkillDiscovery:
    def setup_method(self) -> None:
        self.skills = discover_skills()

    def test_skills_discovered(self) -> None:
        assert len(self.skills) > 0, "No skills found"

    def test_expected_skills_exist(self) -> None:
        found = [s.frontmatter.name for s in self.skills]
        for expected in EXPECTED_SKILLS:
            assert expected in found
