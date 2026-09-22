"""Check that the five-lesson public package stays small and navigable."""

from pathlib import Path
import hashlib
import json
import re
import unittest
import zipfile
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
COURSE_URL = "https://www.crowdsupply.com/neuradock/neuradock-eeg-workstation"


class PublicationTests(unittest.TestCase):
    def test_exactly_five_clean_notebooks(self) -> None:
        notebooks = sorted((ROOT / "notebooks").glob("[0-9][0-9]-*.ipynb"))
        self.assertEqual([p.name[:2] for p in notebooks], ["01", "02", "03", "04", "05"])
        for path in notebooks:
            book = json.loads(path.read_text(encoding="utf-8"))
            for cell in book["cells"]:
                if cell["cell_type"] == "code":
                    self.assertIsNone(cell["execution_count"])
                    self.assertEqual(cell["outputs"], [])

    def test_homepage_leads_to_subscription_and_license(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(COURSE_URL, readme[:1500])
        self.assertIn("academic and non-commercial", readme[:1500])
        self.assertIn("launch updates", readme[:1500])
        self.assertIn("slides/00-neuradock-eeg-101-five-lesson-lecture.pptx", readme)
        self.assertTrue((ROOT / "LICENSE.md").is_file())

    def test_local_markdown_links_exist(self) -> None:
        pages = [ROOT / "README.md", *(ROOT / "tutorials").glob("lesson-0[1-5]*.md")]
        for page in pages:
            content = page.read_text(encoding="utf-8")
            for raw in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)|!\[[^]]*\]\(([^)]+)\)", content):
                target = raw[0] or raw[1]
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("#"):
                    continue
                destination = (page.parent / unquote(parsed.path)).resolve()
                with self.subTest(page=page.name, target=target):
                    self.assertTrue(destination.exists())

    def test_only_approved_recordings_and_complete_slides(self) -> None:
        expected = {
            "recording-01.txt": "1c7cf69cf4572aa96b3452f2febb176c8c2a024eaf0e95812b22edda881006bb",
            "recording-02.txt": "23a8e68b331a86ed7eb79056b580a972bdb9ee74d189e881316f0c7ead35db54",
        }
        actual = list((ROOT / "data" / "teaching").rglob("*.txt"))
        self.assertEqual({p.name for p in actual}, set(expected))
        for path in actual:
            with self.subTest(recording=path.name):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected[path.name])
        deck = ROOT / "slides" / "00-neuradock-eeg-101-five-lesson-lecture.pptx"
        with zipfile.ZipFile(deck) as archive:
            names = archive.namelist()
        slides = [name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        notes = [name for name in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)]
        self.assertEqual(len(slides), 30)
        self.assertEqual(len(notes), 30)
        self.assertTrue((ROOT / "slides" / "01-from-synchronized-neurons-to-measurable-eeg.pptx").is_file())

    def test_no_old_course_app(self) -> None:
        self.assertFalse((ROOT / "src" / "neuradock_eeg101" / "feedback_app.py").exists())


if __name__ == "__main__":
    unittest.main()
