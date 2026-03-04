import tempfile
import unittest
from pathlib import Path

from src.dsipy.shared.vcard import generate_opml_from_vcards


class TestGenerateOpmlFromVcards(unittest.TestCase):
    def test_generates_opml_when_vcards_have_x_feed(self):
        vcard_content = """BEGIN:VCARD
VERSION:4.0
FN:Alice Example
X-FEED:https://example.com/feed.xml
END:VCARD
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            vcard_path = Path(tmp_dir) / "alice.vcf"
            vcard_path.write_text(vcard_content, encoding="utf-8")

            opml_xml = generate_opml_from_vcards([vcard_path])

        self.assertIn("<opml", opml_xml)
        self.assertIn("Alice Example", opml_xml)
        self.assertIn("https://example.com/feed.xml", opml_xml)

    def test_raises_when_no_vcard_contains_feed_url(self):
        vcard_content = """BEGIN:VCARD
VERSION:4.0
FN:Bob Example
END:VCARD
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            vcard_path = Path(tmp_dir) / "bob.vcf"
            vcard_path.write_text(vcard_content, encoding="utf-8")

            with self.assertRaises(ValueError):
                generate_opml_from_vcards([vcard_path])

    def test_raises_when_no_vcards_provided(self):
        with self.assertRaises(ValueError):
            generate_opml_from_vcards([])

    def test_generates_opml_with_multiple_vcards(self):
        vcard_content_1 = """BEGIN:VCARD
VERSION:4.0
FN:Alice Example
X-FEED:https://example.com/feed1.xml
END:VCARD
"""
        vcard_content_2 = """BEGIN:VCARD
VERSION:4.0
FN:Bob Example
X-FEED:https://example.com/feed2.xml
END:VCARD
"""

        with tempfile.TemporaryDirectory() as tmp_dir:
            vcard_path_1 = Path(tmp_dir) / "alice.vcf"
            vcard_path_1.write_text(vcard_content_1, encoding="utf-8")
            vcard_path_2 = Path(tmp_dir) / "bob.vcf"
            vcard_path_2.write_text(vcard_content_2, encoding="utf-8")

            opml_xml = generate_opml_from_vcards([vcard_path_1, vcard_path_2])

        self.assertIn("<opml", opml_xml)
        self.assertIn("Alice Example", opml_xml)
        self.assertIn("Bob Example", opml_xml)
        self.assertIn("https://example.com/feed1.xml", opml_xml)
        self.assertIn("https://example.com/feed2.xml", opml_xml)


if __name__ == "__main__":
    unittest.main()
