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
PAGES = {"home": "index.html", "projects": "projects/index.html", "about": "about/index.html", "cv": "cv/index.html"}
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
        self.media = []
        self.videos = []
        self.dialogs = []
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
        if tag == "dialog":
            self.dialogs.append(attrs.get("id", ""))
        if tag == "video":
            in_dialog = any(name == "dialog" for name, _ in self.stack)
            self.videos.append({**attrs, "in_dialog": in_dialog})
        if tag == "video" and attrs.get("poster"):
            self.media.append(attrs["poster"])
        if tag == "source" and attrs.get("src"):
            self.media.append(attrs["src"])
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

    def test_nav_has_projects_about_and_cv(self):
        targets = ["projects/index.html", "about/index.html", "cv/index.html"]
        for page in PAGES:
            nav = [link for link in parse(page).links if link["in_nav"]]
            self.assertEqual([link["text"].strip() for link in nav], ["Projects", "About", "CV"], page)
            for link, target in zip(nav, targets):
                self.assertEqual(resolve(page, link["href"]), ROOT / target, page)

    def test_nav_marks_the_current_page(self):
        for page in ("projects", "about", "cv"):
            html = (ROOT / PAGES[page]).read_text(encoding="utf8")
            current = re.findall(r'<a href="([^"]*)" aria-current="page">', html)
            self.assertEqual(len(current), 1, page)
            self.assertEqual(resolve(page, current[0]), ROOT / PAGES[page], page)

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

    def test_only_the_robot_arm_tile_is_clickable(self):
        home = parse("home")
        self.assertEqual([link["href"] for link in home.links if link["in_grid"]], ["#autowelder"])
        self.assertNotIn("onclick", (ROOT / "index.html").read_text(encoding="utf8"))
        html = (ROOT / "index.html").read_text(encoding="utf8")
        self.assertRegex(html, r'href="#autowelder"[^>]*><img src="assets/img/tile-17\.svg"')

    def test_autowelder_project_pop_up(self):
        home = parse("home")
        self.assertIn("autowelder", home.dialogs)
        text = " ".join(home.text)
        self.assertIn("Viam: Robotics Hackathon - AutoWelder", text)
        for detail in ("A pick and place station for welders",
                       "reads the gap between the two steels from the camera image",
                       "A new table layout only needs a fresh scan", "Results", "Isaac Sim",
                       "RealSense D435 depth camera", "Software"):
            self.assertIn(detail, text)
        self.assertNotIn("YOLO", text)
        self.assertIn("assets/projects/autowelder/demo.mp4", home.media)
        self.assertIn("assets/projects/autowelder/poster.jpg", home.media)
        photos = [img for img in home.images if img["src"] == "assets/projects/autowelder/station.jpg"]
        self.assertEqual(len(photos), 1)
        self.assertTrue((photos[0]["alt"] or "").strip())
        self.assertIn(("assets/js/project.js", None), home.scripts)

    def test_robot_arm_tile_turns_over_to_the_project_on_hover(self):
        home = parse("home")
        self.assertIn(("assets/js/tile-hover.js", "module"), home.scripts)
        html = (ROOT / "index.html").read_text(encoding="utf8")
        tile = re.search(r'<div class="cell tile tile-link">.*?</div>', html, re.S).group(0)
        self.assertRegex(tile, r'<span class="tile-back" aria-hidden="true">.*AutoWelder.*</span>')
        css = (ROOT / "assets/css/style.css").read_text(encoding="utf8")
        self.assertIn(".tile-link.is-turned a", css)
        self.assertIn("backface-visibility: hidden", css)

    def test_projects_page_lists_autowelder_with_its_video(self):
        projects = parse("projects")
        text = " ".join(projects.text)
        for detail in ("Projects", "October 2026", "AutoWelder",
                       "A pick and place station for welders", "Viam robotics hackathon"):
            self.assertIn(detail, text)
        self.assertNotIn("[", text, "no placeholder rows on the live page")
        self.assertIn("#autowelder", [link["href"] for link in projects.links if not link["in_nav"]])
        html = (ROOT / "projects/index.html").read_text(encoding="utf8")
        self.assertRegex(html, r'<time [^>]*datetime="2026-10"[^>]*>October 2026</time>')

    def test_project_list_videos_play_only_when_asked(self):
        listed = [video for video in parse("projects").videos if not video["in_dialog"]]
        self.assertEqual(len(listed), 1)
        video = listed[0]
        self.assertNotIn("autoplay", video)
        self.assertEqual(video.get("preload"), "none")
        self.assertIn("controls", video)
        self.assertEqual(video.get("poster"), "../assets/projects/autowelder/poster.jpg")
        self.assertTrue((video.get("aria-label") or "").strip())

    def test_projects_page_pop_up_matches_the_home_one(self):
        def dialog(page):
            html = (ROOT / PAGES[page]).read_text(encoding="utf8")
            found = re.search(r'<dialog class="project" id="autowelder".*?</dialog>', html, re.S).group(0)
            return found.replace('"../assets/', '"assets/')
        self.assertEqual(dialog("projects"), dialog("home"))
        self.assertIn(("../assets/js/project.js", None), parse("projects").scripts)

    def test_project_media_is_light_and_has_no_location(self):
        folder = ROOT / "assets/projects/autowelder"
        video = (folder / "demo.mp4").read_bytes()
        self.assertLess(len(video), 50 * 1024 * 1024, "GitHub warns above 50 MB")
        self.assertNotIn(b"com.apple.quicktime", video)
        for name in ("poster.jpg", "station.jpg"):
            self.assertNotIn(b"Exif\0\0", (folder / name).read_bytes(), name)

    def test_home_grid_shape(self):
        home = parse("home")
        tiles = [img for img in home.images if img["in_grid"]]
        self.assertEqual(home.cells, 40)
        self.assertEqual(len(tiles), 1)
        for tile in tiles:
            self.assertTrue((tile["alt"] or "").strip(), f"tile without alt: {tile['src']}")
            self.assertTrue(resolve("home", tile["src"]).is_file(), tile["src"])

    def test_every_home_tile_opens_a_project(self):
        html = (ROOT / "index.html").read_text(encoding="utf8")
        tiles = re.findall(r'<div class="cell tile[^"]*">.*?</a></div>', html, re.S)
        self.assertTrue(tiles)
        for tile in tiles:
            self.assertIn("tile-link", tile, f"tile without a project: {tile}")
            self.assertRegex(tile, r'<a href="#[a-z-]+"', tile)

    def test_home_shows_the_robot_arm_at_every_width(self):
        tiles = {img["src"]: img["alt"] for img in parse("home").images if img["in_grid"]}
        self.assertIn("robot arm", tiles.get("assets/img/tile-17.svg", ""))
        self.assertNotIn("assets/img/tile-10.svg", tiles)
        html = (ROOT / "index.html").read_text(encoding="utf8")
        self.assertRegex(html, r'<div class="cell tile tile-link"><a [^>]*><img src="assets/img/tile-17\.svg"')

    def test_local_references_resolve(self):
        for page in PAGES:
            parsed = parse(page)
            refs = [link["href"] for link in parsed.links]
            refs += [img["src"] for img in parsed.images] + parsed.iframes + parsed.assets + parsed.pdfs + parsed.media
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
