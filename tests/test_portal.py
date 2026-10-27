"""Browser smoke test of the web portal, run only with VIS_WORKFLOW_BROWSER set.

VIS_WORKFLOW_BROWSER=chromium uses Playwright's Chromium (`playwright install chromium`); another value is an
installed browser channel, e.g. msedge. Needs the `browser` extra and `python web/build.py`.
"""
import functools
import http.server
import os
import threading
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest

from conftest import FIXTURES, load_fixture, nodes
from vis_workflow import node_descriptions, to_mermaid
from vis_workflow.cli import make_server
from vis_workflow.sources import portal_url

BROWSER = os.environ.get("VIS_WORKFLOW_BROWSER")
pytestmark = pytest.mark.skipif(not BROWSER, reason="set VIS_WORKFLOW_BROWSER to run the browser test")
sync_api = pytest.importorskip("playwright.sync_api") if BROWSER else None
WEB = Path(__file__).parent.parent / "web"


def serve(server):
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    return server


def test_portal_renders_descriptor_from_view_server():
    assert (WEB / "wheels" / "wheels.json").exists(), "Build the portal's wheels first: python web/build.py"
    name = "wb_measurements_config.yaml"
    portal = serve(http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))))
    # A different port, so the portal fetches cross-origin as with `vis-workflow view`
    descriptor = serve(make_server(FIXTURES / name, 0))
    errors = []
    try:
        with sync_api.sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel=None if BROWSER == "chromium" else BROWSER)
            page = browser.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(portal_url(f"http://127.0.0.1:{descriptor.server_port}/{name}",
                                 f"http://127.0.0.1:{portal.server_port}/"))
            # Pyodide and its packages come from the CDN: allow for a slow first load
            page.wait_for_function(
                "!document.getElementById('result').hidden"
                " || document.getElementById('status').classList.contains('error')",
                timeout=180_000)
            status = page.inner_text("#status")
            rendered = page.locator("#diagram svg .node").count()
            hints = page.locator("#diagram svg .node > title").count()
            with page.expect_download() as download:
                page.click("#download-png")
            png = Path(download.value.path()).read_bytes()
            with page.expect_download() as download:
                page.click("#download")
            svg = Path(download.value.path()).read_text(encoding="utf-8")
            # The PNG's plain-label render must not leak into the on-screen diagram's HTML labels
            page.select_option("#params", "beginner")
            page.wait_for_timeout(500)
            html_labels = page.locator("#diagram svg foreignObject").count()
            browser.close()
    finally:
        portal.shutdown()
        descriptor.shutdown()
    assert status == ""
    assert errors == []
    assert rendered == len(nodes(to_mermaid(load_fixture(name))))
    assert hints == len(node_descriptions(load_fixture(name)))
    assert png.startswith(b"\x89PNG") and len(png) > 10_000
    # A standalone SVG file must be well-formed XML, unlike SVG inline in HTML
    assert ElementTree.fromstring(svg).tag == "{http://www.w3.org/2000/svg}svg"
    assert html_labels > 0
