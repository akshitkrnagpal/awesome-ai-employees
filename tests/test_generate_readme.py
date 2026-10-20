from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import generate_readme


class ReadmeIconTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "assets" / "company-icons").mkdir(parents=True)
        root_patch = patch.object(generate_readme, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def test_embeds_cached_icon_with_fixed_size_beside_company_name(self):
        path = "assets/company-icons/acme.png"
        (self.root / path).touch()
        result = generate_readme.company_cell("Acme", {"Acme": {"path": path}})
        self.assertEqual(
            result,
            '<img src="assets/company-icons/acme.png" '
            'width="20" height="20" align="absmiddle" alt=""> Acme',
        )

    def test_missing_or_unavailable_icons_leave_plain_company_names(self):
        for icons in (
            {},
            {"Acme": {"kind": "initials"}},
            {"Acme": {"path": "assets/company-icons/missing.png"}},
        ):
            with self.subTest(icons=icons):
                self.assertEqual(generate_readme.company_cell("Acme", icons), "Acme")

    def test_encodes_image_path_without_breaking_markdown_cells(self):
        path = "assets/company-icons/acme & co.png"
        (self.root / path).touch()
        result = generate_readme.company_cell("Acme | Co", {"Acme | Co": {"path": path}})
        self.assertIn('src="assets/company-icons/acme%20%26%20co.png"', result)
        self.assertTrue(result.endswith(r"Acme \| Co"))

    def test_rejects_icon_paths_outside_the_cache(self):
        for path in ("/tmp/icon.png", "assets/company-icons/../../secret.png"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    generate_readme.company_cell("Acme", {"Acme": {"path": path}})

    def test_absent_manifest_does_not_require_icon_refresh(self):
        with patch.object(generate_readme, "ICON_MANIFEST_PATH", self.root / "missing.json"):
            self.assertEqual(generate_readme.read_icon_manifest(), {})

    def test_generated_tables_keep_links_descriptions_and_text_fallbacks(self):
        rows = [
            {
                "rank": "1",
                "category": "Sales",
                "company": "Acme",
                "ai_employee_angle": "Research and outreach.",
                "link": "https://example.com/",
            }
        ]
        listing = generate_readme.generated_listing(rows, {})
        self.assertIn(
            "| 1 | Acme | Research and outreach. | https://example.com/ |", listing
        )
        self.assertIn("| # | Company | AI employee angle | Link |", listing)


if __name__ == "__main__":
    unittest.main()
