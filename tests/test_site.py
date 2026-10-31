"""Smoke checks for the static site: structure, navigation, tiles and assets.

Run from the repository root:  python3 -m unittest discover -s tests -v
"""
import posixpath
import re
import shutil
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {"home": "index.html", "about": "about/index.html", "cv": "cv/index.html"}
VOID = {"img", "link", "meta", "br", "hr", "input", "source"}
EXTERNAL = ("http://", "https://", "mailto:", "tel:", "#")
# The repository is public: no phone, email or private repository names in text files.
PRIVATE = re.compile(r"mario\.lavina00|\(310\)\s*569|310[-. ]?569[-. ]?3370|mailto:[^\s<>]*@|career-application", re.I)
TEXT_SUFFIXES = {".html", ".md", ".css", ".js", ".py", ".svg", ".txt"}


class PageParser(HTMLParser):
    """Collects links, images and iframes together with where they sit."""

    def __init__(self):
        super().__init__()
        self.stack = []
        self.links = []
        self.images = []
        self.iframes = []
        self.scripts = []
        self.assets = []
        self.pdfs = []
        self.cells = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        in_nav = any(name == "nav" for name, _ in self.stack)
        in_grid = any("grid" in cls for _, cls in self.stack)
        if tag == "a":
            self.links.append({"href": attrs.get("href", ""), "in_nav": in_nav,
                               "in_grid": in_grid, "class": classes, "text": ""})
        if tag == "img":
            self.images.append({"src": attrs.get("src", ""), "alt": attrs.get("alt"),
                                "in_grid": in_grid})
        if tag == "iframe":
            self.iframes.append(attrs.get("src", ""))
        if tag == "link" and attrs.get("href"):
            self.assets.append(attrs["href"])
        if tag == "script" and attrs.get("src"):
            self.scripts.append((attrs["src"], attrs.get("type")))
            self.assets.append(attrs["src"])
        if attrs.get("data-pdf"):
            self.pdfs.append(attrs["data-pdf"])
        if "cell" in classes:
            self.cells += 1
        if tag not in VOID:
            self.stack.append((tag, classes))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.text.append(data)
        if self.links and any(name == "a" for name, _ in self.stack):
            self.links[-1]["text"] += data


def parse(page):
    parser = PageParser()
    parser.feed((ROOT / PAGES[page]).read_text(encoding="utf8"))
    return parser


def resolve(page, ref):
    """Resolve a relative reference from a page to a path inside the repo."""
    base = posixpath.dirname(PAGES[page])
    target = posixpath.normpath(posixpath.join(base, ref.split("#")[0].split("?")[0]))
    if ref.endswith("/") or target in (".", ""):
        target = posixpath.join(target, "index.html")
    return ROOT / target


class SiteTest(unittest.TestCase):
    def test_pages_exist(self):
        for page, path in PAGES.items():
            self.assertTrue((ROOT / path).is_file(), f"{page} page missing: {path}")

    def test_nav_has_only_about_and_cv(self):
        for page in PAGES:
            nav = [link for link in parse(page).links if link["in_nav"]]
            self.assertEqual([link["text"].strip() for link in nav], ["About", "CV"], page)
            self.assertEqual(resolve(page, nav[0]["href"]), ROOT / "about/index.html", page)
            self.assertEqual(resolve(page, nav[1]["href"]), ROOT / "cv/index.html", page)

    def test_no_menu_button(self):
        for page in PAGES:
            self.assertNotIn("menu", " ".join(parse(page).text).lower(), page)

    def test_logo_links_home(self):
        for page in PAGES:
            logo = [link for link in parse(page).links if "wordmark" in link["class"]]
            self.assertEqual(len(logo), 1, page)
            self.assertEqual(resolve(page, logo[0]["href"]), ROOT / "index.html", page)

    def test_wordmark_shows_the_name_as_two_words(self):
        for page in PAGES:
            logo = [link for link in parse(page).links if "wordmark" in link["class"]]
            self.assertEqual(logo[0]["text"].strip(), "Mario Lavina", page)

    def test_home_tiles_are_not_clickable(self):
        home = parse("home")
        self.assertEqual([link for link in home.links if link["in_grid"]], [])
        self.assertNotIn("onclick", (ROOT / "index.html").read_text(encoding="utf8"))

    def test_home_grid_shape(self):
        home = parse("home")
        tiles = [img for img in home.images if img["in_grid"]]
        self.assertEqual(home.cells, 40)
        self.assertEqual(len(tiles), 16)
        for tile in tiles:
            self.assertTrue((tile["alt"] or "").strip(), f"tile without alt: {tile['src']}")
            self.assertTrue(resolve("home", tile["src"]).is_file(), tile["src"])

    def test_home_shows_the_robot_arm_at_every_width(self):
        tiles = {img["src"]: img["alt"] for img in parse("home").images if img["in_grid"]}
        self.assertIn("robot arm", tiles.get("assets/img/tile-17.svg", ""))
        self.assertNotIn("assets/img/tile-10.svg", tiles)
        html = (ROOT / "index.html").read_text(encoding="utf8")
        self.assertIn('<div class="cell tile"><img src="assets/img/tile-17.svg"', html)

    def test_local_references_resolve(self):
        for page in PAGES:
            parsed = parse(page)
            refs = [link["href"] for link in parsed.links]
            refs += [img["src"] for img in parsed.images] + parsed.iframes + parsed.assets + parsed.pdfs
            for ref in refs:
                if ref and not ref.startswith(EXTERNAL):
                    self.assertTrue(resolve(page, ref).exists(), f"{page}: {ref}")

    def test_no_private_contact_details(self):
        for path in ROOT.rglob("*"):
            skipped = {".git", "tests", "vendor"} & set(path.relative_to(ROOT).parts)
            if path.is_file() and path.suffix in TEXT_SUFFIXES and not skipped:
                found = PRIVATE.search(path.read_text(encoding="utf8"))
                self.assertIsNone(found, f"{path.relative_to(ROOT)} contains {found and found.group(0)!r}")

    def test_cv_pdf_is_drawn_inside_the_page(self):
        cv = parse("cv")
        self.assertEqual(cv.iframes, [], "the CV is drawn in the page, not in a browser frame")
        self.assertEqual(len(cv.pdfs), 1)
        self.assertEqual(resolve("cv", cv.pdfs[0]).read_bytes()[:5], b"%PDF-")
        self.assertIn(("../assets/js/cv.js", "module"), cv.scripts)
        for name in ("pdf.min.js", "pdf.worker.min.js", "LICENSE"):
            self.assertTrue((ROOT / "assets/vendor/pdfjs" / name).is_file(), name)

    @unittest.skipUnless(shutil.which("node"), "node is needed to run the viewer tests")
    def test_cv_viewer_never_draws_a_page_twice(self):
        result = subprocess.run(["node", "--test", "tests/"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
