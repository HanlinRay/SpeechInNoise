"""Tests for static/scoring_status.js (list position and words scored).

The browser tests load the real azbio_mandarin.html test page in headless
Chrome, with every /api call blocked, and drive the page's own code. They are
skipped when Playwright or a browser is not installed.

    pip install playwright && playwright install chromium
    pytest scoring_status_test.py
"""
import functools
import http.server
import threading

import pytest

from storage import relpath

playwright_api = pytest.importorskip("playwright.sync_api")

SENTENCE = "我 知道 一家 很棒的 小店 一起 去吧"
MANDARIN = "audio/azbio_mandarin/AzBio_Mandarin_10DBSNR_List1_Sentence-03.wav"


@pytest.fixture(scope="module")
def static_server():
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=relpath("static"))
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


@pytest.fixture
def page(browser, static_server):
    page = browser.new_page()
    # The page calls the experiment API on load; there is no server here.
    page.route("**/api/**", lambda route: route.abort())
    page.route("**/fonts.*/**", lambda route: route.abort())
    page.goto(f"{static_server}/azbio_mandarin.html")
    page.wait_for_function("window.ScoringStatus !== undefined")
    yield page
    page.close()


def parse(page, url):
    return page.evaluate("u => ScoringStatus.parseAudioName(u)", url)


@pytest.mark.parametrize("url, expected", [
    (MANDARIN,
     {"list": 1, "unit": "Sentence", "item": 3, "condition": "10 dB SNR"}),
    ("audio/azbio/AzBio_10dBSNR_List6_Sentence-16.wav",
     {"list": 6, "unit": "Sentence", "item": 16, "condition": "10 dB SNR"}),
    ("audio/azbio_quiet/AzBio_Quiet_List1_Sentence-1.wav",
     {"list": 1, "unit": "Sentence", "item": 1, "condition": "Quiet"}),
    ("audio/cnc/CNC_List1_Word1_Goose.wav",
     {"list": 1, "unit": "Word", "item": 1, "condition": None}),
    ("audio/win/WIN_T6L1_Word1_Cool.wav",
     {"list": 1, "unit": "Word", "item": 1, "condition": None}),
    ("audio/quicksin/List01Sentence01.wav",
     {"list": 1, "unit": "Sentence", "item": 1, "condition": None}),
    ("blob:http://x/0b6a", None),
    ("", None),
])
def test_parse_every_file_name_pattern_in_metadata(page, url, expected):
    assert parse(page, url) == expected


def test_progress_shows_the_list_position_with_the_total(page):
    # what the page's own code does: load() with the start response, then
    # play the first audio
    page.evaluate("""u => {
        audio.load({name: "test-x", answer: ["我 知道", "火车站 有车"],
                    levels: 20});
        AudioPrefetch.prototype.playback_debug.call(audio, u);
    }""", MANDARIN)
    assert page.inner_text("#trial-progress") == (
        "List 1 · Sentence 3 of 20 · 10 dB SNR")


def test_progress_without_total_from_an_older_server(page):
    page.evaluate("""u => {
        audio.load({name: "test-x", answer: ["我 知道", "火车站 有车"]});
        AudioPrefetch.prototype.playback_debug.call(audio, u);
    }""", MANDARIN)
    assert page.inner_text("#trial-progress") == (
        "List 1 · Sentence 3 · 10 dB SNR")


def count(page):
    page.wait_for_timeout(50)
    return page.inner_text("#scored-count")


def test_count_follows_clicks_and_all_none(page):
    page.evaluate("s => audio.options(s)", SENTENCE)
    assert count(page) == "0 of 7 words scored"
    page.click(".options-case > div:nth-child(2) .option-on")
    assert count(page) == "1 of 7 words scored · 1 correct"
    page.click("#result-none")
    assert count(page) == "7 of 7 words scored · 0 correct"
    assert "complete" in page.get_attribute("#scored-count", "class")
    page.click("#result-all")
    assert count(page) == "7 of 7 words scored · 7 correct"


def test_count_resets_for_the_next_sentence(page):
    page.evaluate("s => audio.options(s)", SENTENCE)
    page.click("#result-all")
    assert count(page).startswith("7 of 7")
    page.evaluate("() => audio.options('火车站 有车 可以')")
    assert count(page) == "0 of 3 words scored"
    assert "complete" not in (page.get_attribute("#scored-count", "class") or "")


def test_count_is_hidden_before_any_words(page):
    assert page.is_hidden("#scored-count")


def test_nothing_sent_changes(page):
    """The annotations the page sends are read from the same radios."""
    page.evaluate("s => audio.options(s)", SENTENCE)
    page.click("#result-all")
    page.click(".options-case > div:nth-child(1) .option-off")
    assert page.evaluate("() => recorder.aux_data()") == (
        [False] + [True] * 6)
