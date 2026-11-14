"""Verify the real WASM detector and the responsive project page in Chrome."""
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
from urllib.parse import urljoin

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import WebHandler


class QuietHandler(WebHandler):
    def log_message(self, *args):
        pass


def verify(browser, url, width, height, theme, columns):
    page = browser.new_page(
        viewport={"width": width, "height": height}, color_scheme=theme,
        has_touch=columns < 3, permissions=["camera"],
    )
    page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url, wait_until="domcontentloaded")
    expect(page.locator("html")).to_have_attribute("data-theme", theme)
    assert page.evaluate("document.documentElement.scrollWidth === innerWidth")
    assert page.locator(".project-gallery").evaluate(
        "(el) => getComputedStyle(el).gridTemplateColumns.split(' ').length"
    ) == columns
    page.locator("#project-theme").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark" if theme == "light" else "light")
    page.locator("#project-theme").click()
    if columns < 3:
        page.locator("#project-menu").click()
        expect(page.locator(".project-nav")).to_be_visible()
    page.locator(".project-nav").get_by_text("Gallery").click()
    expect(page).to_have_url(url + "#gallery")
    expect(page.locator("#project-top")).to_be_visible()
    cards = page.locator(".project-gallery figure:visible")
    expect(cards).to_have_count(24)
    search = page.locator("#gallery-search").bounding_box()
    category = page.locator("#gallery-category").bounding_box()
    assert abs(search["y"] - category["y"]) <= 1
    assert abs(search["height"] - category["height"]) <= 1
    assert search["x"] + search["width"] < category["x"]
    page.locator("#gallery-category").select_option("Inference")
    expect(cards).to_have_count(3)
    page.locator("#gallery-search").fill("coordinates")
    expect(cards).to_have_count(1)
    page.locator("#gallery-search").clear()
    cards.locator("a").first.click()
    title = page.locator("#figure-title")
    expect(title).to_have_text("ONNX detection on a test image")
    page.locator("#figure-next").click()
    expect(title).to_have_text("The letterboxed model input")
    page.locator("#figure-prev").click()
    expect(title).to_have_text("ONNX detection on a test image")
    page.keyboard.press("ArrowRight")
    expect(title).to_have_text("The letterboxed model input")
    page.locator("#figure-zoom").click()
    assert page.locator(".project-stage").evaluate("(el) => el.scrollWidth > el.clientWidth")
    page.locator("#figure-zoom").click()
    if columns < 3:
        image = page.locator(".project-stage img")
        page.wait_for_function("document.querySelector('.project-stage img').naturalWidth > 0")
        box = image.bounding_box()
        x, y = box["x"] + box["width"] * .7, box["y"] + box["height"] * .5
        cdp = page.context.new_cdp_session(page)
        for kind, points in [
            ("touchStart", [{"x": x, "y": y}]),
            ("touchMove", [{"x": x - 85, "y": y}]),
            ("touchEnd", []),
        ]:
            cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": points})
        expect(title).to_have_text("Detector output and coordinates")
    page.keyboard.press("Escape")
    expect(page.locator("#project-viewer")).to_be_hidden()
    if width == 390:
        slider = page.locator('[aria-controls="live-links"]')
        slider.focus()
        page.keyboard.press("End")
        assert page.locator("#live-links").evaluate("(el) => el.scrollLeft") > 0
    if width == 1440 and theme == "light":
        page.wait_for_function("document.querySelector('.simulation-player').readyState >= 2")
        video = page.locator(".simulation-player")
        assert video.evaluate("(el) => el.videoWidth") == 960
        video.evaluate("(el) => el.play()")
        page.wait_for_function("document.querySelector('.simulation-player').currentTime > 0")
        video.evaluate("(el) => el.pause()")
        targets = page.locator("a[href],img[src],script[src],link[href],video[src]").evaluate_all(
            "(els) => [...new Set(els.map(e => e.getAttribute('href') || e.getAttribute('src')))]"
        )
        for target in targets:
            if target.startswith("#"):
                assert page.locator(f'[id="{target[1:]}"]').count() == 1, target
            elif not target.startswith(("https://", "data:")):
                assert page.request.get(urljoin(url, target)).ok, target
        for link in page.locator("a[download]").all():
            with page.expect_download() as download:
                link.click()
            assert download.value.failure() is None
        page.locator("#sample-start").click()
        expect(page.locator("#target-state")).to_have_text("TRACKING", timeout=30000)
        expect(page.locator("#coordinates")).to_contain_text("X ")
        expect(page.locator("#mode-badge")).to_have_text("IMAGE")
        expect(page.locator("#frames")).to_have_text("1")
        page.locator("#confidence").evaluate("(el) => { el.value = 90; el.dispatchEvent(new Event('input')); }")
        expect(page.locator("#target-state")).to_have_text("NO TARGET")
        page.locator("#confidence").evaluate("(el) => { el.value = 35; el.dispatchEvent(new Event('input')); }")
        expect(page.locator("#target-state")).to_have_text("TRACKING")
        expect(page.locator("#frames")).to_have_text("1")
        with page.expect_download() as snapshot:
            page.locator("#snapshot").click()
        assert snapshot.value.failure() is None
        page.locator("#stop").click()
        page.locator("#image-picker").set_input_files(ROOT / "docs/samples/test-shuttle.jpg")
        expect(page.locator("#target-state")).to_have_text("TRACKING", timeout=30000)
        expect(page.locator("#frames")).to_have_text("1")
        page.locator("#stop").click()
        page.locator("#image-picker").set_input_files(
            {"name": "broken.png", "mimeType": "image/png", "buffer": b"not a PNG"}
        )
        expect(page.locator("#status")).to_contain_text("Could not open that image")
        page.locator("#start").click()
        expect(page.locator("#mode-badge")).to_have_text("LIVE", timeout=30000)
        page.wait_for_function("Number(document.querySelector('#frames').textContent) > 0")
        page.locator("#pause").click()
        expect(page.locator("#paused-overlay")).to_be_visible()
        page.locator("#stop").click()
        expect(page.locator("#mode-badge")).to_have_text("STANDBY")
    page.evaluate("scrollTo(0, document.body.scrollHeight)")
    page.locator("#project-top").click()
    page.wait_for_function("scrollY === 0")
    assert not errors, errors
    print(f"Passed {width}x{height} {theme} ({columns} gallery columns)")
    page.close()


def verify_direct_preview(browser):
    page = browser.new_page(viewport={"width": 390, "height": 844}, color_scheme="dark")
    page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
    url = (ROOT / "docs/index.html").as_uri()
    page.goto(url, wait_until="domcontentloaded")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    page.get_by_role("button", name="Switch to light theme").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "light")
    expect(page.locator("#project-theme .project-moon")).to_be_visible()
    page.locator("#project-menu").click()
    expect(page.locator(".project-nav")).to_be_visible()
    page.locator(".project-nav").get_by_text("Gallery").click()
    expect(page).to_have_url(url + "#gallery")
    page.locator(".brand").click()
    expect(page).to_have_url(url + "#page-top")
    page.wait_for_function("scrollY === 0")
    page.evaluate("scrollTo(0, document.body.scrollHeight)")
    top = page.get_by_role("button", name="Back to top")
    expect(top).to_be_visible()
    assert top.bounding_box()["width"] >= 58
    top.click()
    page.wait_for_function("scrollY === 0")
    expect(top).to_be_hidden()
    print("Passed direct file preview: theme, mobile navigation, brand link, and Back to Top")
    page.close()


def main():
    with ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "docs"))) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/"
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    channel="chrome", args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
                )
                for width, height, columns in [(390,844,1),(768,1024,2),(1440,900,3)]:
                    for theme in ("light","dark"):
                        verify(browser, url, width, height, theme, columns)
                verify_direct_preview(browser)
                browser.close()
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
