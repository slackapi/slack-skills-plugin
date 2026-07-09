from xml.etree.ElementTree import Element

import markdown
from markdown.treeprocessors import Treeprocessor

from tests.skill import discover_skills

# A skill body should have more than one navigable section so that the content
# is scannable and logically organized.
MIN_SECTIONS = 2


class _HeadingCollector(Treeprocessor):
    def run(self, root: Element) -> None:
        # Parsing to a tree (rather than regex on the raw text) keeps ``#``
        # lines inside fenced code blocks from being mistaken for headings.
        self.levels = [
            int(elem.tag[1]) for elem in root.iter() if elem.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}
        ]


def heading_levels(body: str) -> list[int]:
    """Levels of real ATX headings, ignoring ``#`` lines inside code fences."""
    md = markdown.Markdown(extensions=["fenced_code"])
    collector = _HeadingCollector(md)
    md.treeprocessors.register(collector, "heading_collector", 100)
    md.convert(body)
    return collector.levels


class TestMarkdownStructure:
    def setup_method(self) -> None:
        self.skills = discover_skills()

    def test_has_single_top_level_heading(self) -> None:
        for skill in self.skills:
            h1_count = heading_levels(skill.body).count(1)
            assert h1_count == 1, f"{skill.path} should have exactly one H1 heading, found {h1_count}"

    def test_has_section_structure(self) -> None:
        for skill in self.skills:
            h2_count = heading_levels(skill.body).count(2)
            assert h2_count >= MIN_SECTIONS, (
                f"{skill.path} should have at least {MIN_SECTIONS} H2 sections, found {h2_count}"
            )
