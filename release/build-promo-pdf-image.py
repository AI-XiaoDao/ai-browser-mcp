# -*- coding: utf-8 -*-
"""Export promo-poster.html → PDF (with links) + long PNG."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "promo-poster.html"
PDF_OUT = ROOT / "AI-Browser-MCP-Promo-v2.6.pdf"
PNG_OUT = ROOT / "AI-Browser-MCP-Promo-v2.6-long.png"
WIDTH = 1080


def build():
    if not HTML.exists():
        raise SystemExit(f"Missing {HTML}")

    url = HTML.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=120_000)
        page.wait_for_timeout(1500)

        height = page.evaluate("() => document.documentElement.scrollHeight")
        page.set_viewport_size({"width": WIDTH, "height": max(height, 900)})

        page.pdf(
            path=str(PDF_OUT),
            width=f"{WIDTH}px",
            height=f"{height}px",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        page.screenshot(path=str(PNG_OUT), full_page=True, type="png")
        browser.close()

    print(f"PDF: {PDF_OUT} ({PDF_OUT.stat().st_size // 1024} KB)")
    print(f"PNG: {PNG_OUT} ({PNG_OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
