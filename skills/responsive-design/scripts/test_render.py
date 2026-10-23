"""Tests for render.sh, the headless-render wrapper."""
import os
import shutil
import subprocess
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER = os.path.join(HERE, "render.sh")


def run(*args):
    return subprocess.run([RENDER, *args], capture_output=True, text=True)


class DimensionGuards(unittest.TestCase):
    """Chrome silently clamps --window-size to a 500px minimum, so a request
    for 320, 390 or 480 renders at 500 and reports a clean pass that means
    nothing. The wrapper refuses rather than measuring the wrong page."""

    def test_a_width_that_is_not_a_number_is_refused(self):
        r = run("--width", "wide", "--out", "/dev/null", "--url", "about:blank")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--width", r.stderr)
        self.assertNotIn("integer expression expected", r.stderr)

    def test_a_height_that_is_not_a_number_is_refused(self):
        r = run("--width", "900", "--height", "tall",
                "--out", "/dev/null", "--url", "about:blank")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--height", r.stderr)

    def test_width_below_the_clamp_is_refused(self):
        r = run("--width", "320", "--out", "/dev/null", "--url", "about:blank")
        self.assertEqual(r.returncode, 2)
        self.assertIn("500", r.stderr)


class UsageErrors(unittest.TestCase):
    """Every refusal exits 2 and names the argument at fault, so a caller is
    never handed a rendered file that answers a different question."""

    def test_an_unknown_argument_is_refused(self):
        r = run("--widht", "900", "--out", "/dev/null", "--url", "about:blank")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--widht", r.stderr)

    def test_a_missing_out_is_refused(self):
        r = run("--width", "900", "--url", "about:blank")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--out", r.stderr)

    def test_a_missing_url_is_refused(self):
        r = run("--width", "900", "--out", "/dev/null")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--url", r.stderr)

    def test_an_unknown_mode_is_refused(self):
        r = run("--width", "900", "--out", "/dev/null",
                "--url", "about:blank", "--mode", "pdf")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--mode", r.stderr)

    def test_an_unknown_colour_scheme_is_refused(self):
        r = run("--width", "900", "--out", "/dev/null", "--url", "about:blank",
                "--color-scheme", "sepia")
        self.assertEqual(r.returncode, 2)
        self.assertIn("sepia", r.stderr)

    def test_a_source_file_that_is_not_there_is_refused(self):
        r = run("--width", "900", "--out", "/dev/null", "--url", "/nope/absent.html")
        self.assertEqual(r.returncode, 2)
        self.assertIn("absent.html", r.stderr)

    def test_fonts_without_dom_mode_is_refused(self):
        r = run("--width", "900", "--out", "/dev/null",
                "--url", "about:blank", "--fonts")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--mode dom", r.stderr)


CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FIXTURE = "<!doctype html><meta charset=utf-8><title>t</title><h1>hello</h1>"


@unittest.skipUnless(os.path.exists(CHROME), "Chrome not installed here")
class ScreenshotRender(unittest.TestCase):
    """Chrome writes its output in a couple of seconds and then never exits,
    so a wrapper that waits for the process pays whatever timeout it was
    given. This one polls the output and kills Chrome once it stops growing."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.page = os.path.join(self.dir, "page.html")
        with open(self.page, "w") as f:
            f.write(FIXTURE)
        self.out = os.path.join(self.dir, "shot.png")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_the_chrome_profile_directory_is_taken_away_again(self):
        """Each render needs a throwaway profile; Chrome fills it with about
        3MB, so a run that abandons one leaves that behind every time."""
        import glob
        pattern = os.path.join(tempfile.gettempdir(), "render-sh*")
        before = set(glob.glob(pattern))
        run("--url", self.page, "--out", self.out, "--width", "900")
        self.assertEqual(set(glob.glob(pattern)) - before, set())

    def test_returns_a_written_screenshot_without_waiting_for_chrome_to_exit(self):
        started = time.time()
        r = run("--url", self.page, "--out", self.out, "--width", "900")
        elapsed = time.time() - started
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(self.out), "no output file written")
        self.assertGreater(os.path.getsize(self.out), 0)
        self.assertLess(elapsed, 30, "did not return until Chrome exited")


@unittest.skipUnless(os.path.exists(CHROME), "Chrome not installed here")
class DomRender(unittest.TestCase):
    """Most checks read the DOM after scripts have run, not a picture of it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.page = os.path.join(self.dir, "page.html")
        with open(self.page, "w") as f:
            f.write(FIXTURE + "<script>document.title='ran'</script>")
        self.out = os.path.join(self.dir, "dom.html")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_dom_mode_captures_the_page_after_its_scripts_ran(self):
        r = run("--url", self.page, "--out", self.out, "--width", "900", "--mode", "dom")
        self.assertEqual(r.returncode, 0, r.stderr)
        dom = open(self.out).read()
        self.assertIn("<h1>hello</h1>", dom)
        self.assertIn("<title>ran</title>", dom)


SCHEME_FIXTURE = (
    "<!doctype html><meta charset=utf-8><pre id=r>pending</pre>"
    "<script>document.getElementById('r').textContent="
    "'dark='+matchMedia('(prefers-color-scheme: dark)').matches</script>"
)


@unittest.skipUnless(os.path.exists(CHROME), "Chrome not installed here")
class ColorScheme(unittest.TestCase):
    """A page can answer the reader's colour scheme, and a review that renders
    only the default one has tested half of it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.page = os.path.join(self.dir, "page.html")
        with open(self.page, "w") as f:
            f.write(SCHEME_FIXTURE)
        self.out = os.path.join(self.dir, "dom.html")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def render(self, *extra):
        r = run("--url", self.page, "--out", self.out,
                "--width", "900", "--mode", "dom", *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        return open(self.out).read()

    def test_dark_is_what_the_page_is_asked_and_light_is_the_default(self):
        self.assertIn("dark=true", self.render("--color-scheme", "dark"))
        self.assertIn("dark=false", self.render("--color-scheme", "light"))
        self.assertIn("dark=false", self.render())


WEBFONT_FIXTURE = (
    "<!doctype html><meta charset=utf-8>"
    '<style>@font-face{font-family:Probey;src:local("Helvetica")}'
    "body{font-family:Probey,sans-serif}</style><h1>hello</h1>"
)


@unittest.skipUnless(os.path.exists(CHROME), "Chrome not installed here")
class FontReport(unittest.TestCase):
    """A page whose fonts arrive over the network lays out one way before they
    land and another way after, so a measurement taken in between is of a page
    nobody will see. The receipt reports faces downloaded over faces declared:
    the declared count alone rises as soon as the stylesheet parses, and stays
    at 57 on a page whose glyphs are still arriving eight at a time."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.page = os.path.join(self.dir, "page.html")
        with open(self.page, "w") as f:
            f.write(WEBFONT_FIXTURE)
        self.out = os.path.join(self.dir, "dom.html")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_receipt_reports_downloaded_over_declared(self):
        r = run("--url", self.page, "--out", self.out,
                "--width", "900", "--mode", "dom", "--fonts")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fonts=1/1", r.stdout)

    def test_a_face_that_never_arrives_is_not_counted_as_downloaded(self):
        page = os.path.join(self.dir, "two.html")
        with open(page, "w") as f:
            f.write(
                "<!doctype html><meta charset=utf-8><style>"
                '@font-face{font-family:Good;src:local("Helvetica")}'
                '@font-face{font-family:Bad;src:url("./absent.woff2") format("woff2")}'
                "body{font-family:Good,sans-serif}h2{font-family:Bad,serif}"
                "</style><h1>hello</h1><h2>world</h2>"
            )
        r = run("--url", page, "--out", self.out,
                "--width", "900", "--mode", "dom", "--fonts")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fonts=1/2", r.stdout)

    def test_the_probe_does_not_survive_into_the_captured_page(self):
        run("--url", self.page, "--out", self.out,
            "--width", "900", "--mode", "dom", "--fonts")
        captured = open(self.out).read()
        self.assertNotIn("__renderProbe", captured)
        self.assertNotIn("document.fonts.ready", captured)
        self.assertNotIn("data-render-fonts", captured)

    def test_a_probe_that_cannot_be_written_fails_loudly(self):
        """The probe copy goes beside the source, so a read-only source
        directory stops it. Reporting ok with an unknown count there would
        hand back a capture of nothing under a success line."""
        locked = tempfile.mkdtemp()
        page = os.path.join(locked, "page.html")
        with open(page, "w") as f:
            f.write(WEBFONT_FIXTURE)
        os.chmod(locked, 0o500)
        try:
            r = run("--url", page, "--out", self.out,
                    "--width", "900", "--mode", "dom", "--fonts")
        finally:
            os.chmod(locked, 0o700)
            shutil.rmtree(locked, ignore_errors=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("render: ok", r.stdout)
        self.assertIn("probe", r.stderr.lower())

    def test_an_interrupted_run_leaves_no_probe_copy_behind(self):
        """The probe copy lands in the caller's own directory, so a run that
        is cut short must not leave one there for them to find later."""
        import glob
        import signal
        proc = subprocess.Popen(
            [RENDER, "--url", self.page, "--out", self.out,
             "--width", "900", "--mode", "dom", "--fonts"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pattern = os.path.join(self.dir, ".render-probe-*.html")
        deadline = time.time() + 10
        while time.time() < deadline and not glob.glob(pattern):
            time.sleep(0.02)
        self.assertTrue(glob.glob(pattern), "probe copy never appeared to interrupt")
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)
        self.assertEqual(glob.glob(pattern), [])

    def test_the_original_page_is_left_alone(self):
        run("--url", self.page, "--out", self.out,
            "--width", "900", "--mode", "dom", "--fonts")
        self.assertEqual(open(self.page).read(), WEBFONT_FIXTURE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
