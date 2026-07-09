import re

from tests.skill import discover_skills


def is_kebab_case(text: str) -> bool:
    # Pattern ensures lowercase alphanumeric chunks separated by a single dash
    pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    return bool(re.match(pattern, text))


class TestFrontmatter:
    def setup_method(self) -> None:
        self.skills = discover_skills()

    def test_required_fields_present(self) -> None:
        for skill in self.skills:
            assert skill.frontmatter.name, f"{skill.path} is missing a frontmatter 'name'"
            assert skill.frontmatter.description, f"{skill.path} is missing a frontmatter 'description'"

    def test_name_matches_directory(self) -> None:
        for skill in self.skills:
            assert skill.frontmatter.name == skill.path.parent.name, (
                f"{skill.path} frontmatter name '{skill.frontmatter.name}' "
                f"does not match directory '{skill.path.parent.name}'"
            )

    def test_name_is_kebab_case(self) -> None:
        for skill in self.skills:
            assert is_kebab_case(skill.frontmatter.name), (
                f"{skill.path} name '{skill.frontmatter.name}' is not valid kebab-case"
            )

    def test_skill_names_are_unique(self) -> None:
        names = [skill.frontmatter.name for skill in self.skills]
        assert len(names) == len(set(names)), f"Duplicate skill names found in: {sorted(names)}"
