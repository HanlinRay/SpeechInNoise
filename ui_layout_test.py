"""Browser tests for the start page, the results page and the rater page.

Each page is loaded from static/ in headless Chrome; the API is answered by
small stubs, so no server or database is needed. Skipped when Playwright or a
browser is not installed.

    pip install playwright && playwright install chromium
    pytest ui_layout_test.py
"""
import functools
import http.server
import json
import pathlib
import re
import threading

import pytest

from storage import relpath

playwright_api = pytest.importorskip("playwright.sync_api")

# The shape of POST /api/lists (from a fresh database).
LISTS = {
    "": "quick",
    "quick": ["en", "en-1", "en-2"],
    "azbio": ["en", "en-1", "en-2"],
    "review": [],
    "azbio_spanish": ["es", "es-1"],
    "azbio_mandarin": ["zh", "zh-1", "zh-2"],
    "azbio_mandarin_quiet": ["zh", "zh-1", "zh-2"],
}

# The shape of GET /api/<project>/recognized: two sessions, two trials each.
RECOGNIZED = [
    {"subject": s, "time": t, "username": u, "upload": f"r{s}{i}",
     "prompt": f"azbio_mandarin/List1_Sentence-0{i}.wav", "transcript": None,
     "answer": "我 知道", "annotations": [True, False], "trial_number": 1}
    for s, t, u in ((3, "2026-11-10 18:00:00", "alice"),
                    (7, "2026-11-12 19:30:00", "bob"))
    for i in (1, 2)
]


class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # review.html loads its files from /jnd/api/static/
        for prefix in ("/jnd/api/static/", "/jnd/static/", "/static/"):
            if path.startswith(prefix):
                path = "/" + path[len(prefix):]
        return super().translate_path(path)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def static_server():
    handler = functools.partial(StaticHandler, directory=relpath("static"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with playwright_api.sync_playwright() as p:
        launched = None
        for kwargs in ({}, {"channel": "chrome"}):
            try:
                launched = p.chromium.launch(**kwargs)
                break
            except Exception:  # browser not installed
                continue
        if launched is None:
            pytest.skip("no Chromium or Chrome available for Playwright")
        yield launched
        launched.close()


def api_stub(route):
    url = route.request.url
    if "/static/" in url:
        return route.continue_()
    if url.endswith("/api/lists"):
        return route.fulfill(status=200, content_type="application/json",
                             body=json.dumps(LISTS))
    if "/recognized" in url:
        return route.fulfill(status=200, content_type="application/json",
                             body=json.dumps(RECOGNIZED))
    return route.abort()


@pytest.fixture
def open_page(browser, static_server):
    pages = []

    def go(name):
        page = browser.new_page()
        page.route("**/api/**", api_stub)
        page.route("**/fonts.*/**", lambda route: route.abort())
        page.goto(f"{static_server}/{name}")
        pages.append(page)
        return page
    yield go
    for page in pages:
        page.close()


def options(page, select):
    return page.eval_on_selector_all(
        f"#{select} option", "els => els.map(e => e.textContent)")


# 1. Start page: language first, then the test -------------------------------

@pytest.fixture
def start_page(open_page):
    page = open_page("index.html")
    page.wait_for_function(
        "document.querySelectorAll('#language option').length > 1")
    return page


def test_languages_are_listed_once_in_order(start_page):
    assert options(start_page, "language") == [
        "All", "English", "Spanish", "Chinese", "Other"]


def test_all_keeps_every_project_and_default(start_page):
    assert options(start_page, "project") == ["Default"] + [
        k for k in LISTS if k]


def test_chinese_shows_only_the_mandarin_tests(start_page):
    start_page.select_option("#language", "Chinese")
    assert options(start_page, "project") == [
        "azbio_mandarin", "azbio_mandarin_quiet"]
    assert options(start_page, "list") == ["Default", "zh", "zh-1", "zh-2"]
    assert start_page.get_attribute("#results", "href") == (
        "recognized.html?user=all&project=azbio_mandarin")


def test_choice_is_kept_when_it_is_still_offered(start_page):
    start_page.select_option("#language", "Chinese")
    start_page.select_option("#project", "azbio_mandarin_quiet")
    start_page.select_option("#language", "All")
    assert start_page.input_value("#project") == "azbio_mandarin_quiet"


# 2. Results page: one collapsed row per session -----------------------------

@pytest.fixture
def results_page(open_page):
    page = open_page("recognized.html?user=all&project=azbio_mandarin")
    page.wait_for_selector("tbody.userinfo:not(.template)")
    return page


def sessions(page):
    return page.eval_on_selector_all(
        "tbody.userinfo:not(.template) .username",
        "els => els.map(e => e.textContent)")


def visible_trials(page):
    return page.eval_on_selector_all(
        "tbody:not(.template):not(.userinfo)",
        "els => els.filter(e => !e.hidden).length")


def test_sessions_start_collapsed_newest_first(results_page):
    assert sessions(results_page) == ["bob", "alice"]
    assert visible_trials(results_page) == 0
    assert results_page.inner_text(
        "tbody.userinfo:not(.template) .toggle") == "2 trials"


def test_no_audio_is_fetched_until_a_session_is_opened(results_page):
    srcs = results_page.eval_on_selector_all(
        "tbody:not(.template) audio", "els => els.map(e => e.src)")
    assert srcs and all(src == "" for src in srcs)


def test_clicking_a_session_opens_and_closes_it(results_page):
    header = results_page.locator("tbody.userinfo:not(.template)").first
    header.locator(".time").click()
    assert visible_trials(results_page) == 2
    assert results_page.eval_on_selector_all(
        "tbody.userinfo:not(.template)",
        "els => els.map(e => e.classList.contains('collapsed'))") == [
            False, True]  # only the clicked session (bob) is open
    srcs = results_page.eval_on_selector_all(
        "tbody:not(.template):not(.userinfo):not([hidden]) audio.prompt",
        "els => els.map(e => e.getAttribute('src'))")
    assert srcs == ["audio/azbio_mandarin/List1_Sentence-01.wav",
                    "audio/azbio_mandarin/List1_Sentence-02.wav"]
    header.locator(".time").click()
    assert visible_trials(results_page) == 0


def test_name_link_still_opens_the_plot(results_page):
    link = results_page.locator("tbody.userinfo:not(.template) .username a")
    assert link.first.get_attribute("href") == "api/azbio_mandarin/plot?user=7"


# C and D. Rater page ---------------------------------------------------------

def test_review_html_has_no_inline_styles_outside_comments():
    html = pathlib.Path(relpath("static", "review.html")).read_text()
    live = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    assert 'style="' not in live


def test_faulty_audio_box_is_below_all_and_none(open_page):
    page = open_page("review.html")
    page.wait_for_function("typeof audio !== 'undefined'")
    page.evaluate("() => audio.options('我 知道 一家')")
    label = page.locator("#unclear-checkbox-label").bounding_box()
    buttons = page.locator("#result-options").bounding_box()
    words = page.locator(".options-case").bounding_box()
    assert words["y"] < buttons["y"] < label["y"]
