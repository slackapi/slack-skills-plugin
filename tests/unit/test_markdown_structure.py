from tests.skill import discover_skills, headings

# A skill body should have more than one navigable section so that the content
# is scannable and logically organized.
MIN_SECTIONS = 2


class TestMarkdownStructure:
    def setup_method(self) -> None:
        self.skills = discover_skills()

    def test_has_single_top_level_heading(self) -> None:
        for skill in self.skills:
            h1s = [h for h in headings(skill.body) if h[0] == 1]
            assert len(h1s) == 1, f"{skill.path} should have exactly one H1 heading, found {len(h1s)}"

    def test_has_section_structure(self) -> None:
        for skill in self.skills:
            h2s = [h for h in headings(skill.body) if h[0] == 2]
            assert len(h2s) >= MIN_SECTIONS, (
                f"{skill.path} should have at least {MIN_SECTIONS} H2 sections, found {len(h2s)}"
            )
