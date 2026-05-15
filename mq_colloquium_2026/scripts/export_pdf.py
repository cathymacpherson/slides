from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
OUT_DIR = ROOT / "exports"
SLIDE_WIDTH = 1600
SLIDE_HEIGHT = 900


def find_browser() -> Path:
    candidates = [
        shutil.which("msedge"),
        shutil.which("msedge.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        shutil.which("chrome"),
        shutil.which("chrome.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError("Could not find Chrome or Edge. Install one browser, then rerun npm run export:pdf.")


def slide_count() -> int:
    text = INDEX.read_text(encoding="utf-8")
    count = len(re.findall(r"<section\b[^>]*class=\"[^\"]*\bslide\b", text, flags=re.IGNORECASE))
    if count == 0:
        raise RuntimeError("No slides found in index.html.")
    return count


def capture_pages(browser: Path, count: int, work_dir: Path) -> list[Path]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("PDF export requires Python Playwright, which is not installed.") from exc

    page_images: list[Path] = []
    with sync_playwright() as playwright:
        browser_instance = playwright.chromium.launch(
            executable_path=str(browser),
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-gpu-sandbox",
                "--disable-dev-shm-usage",
                "--allow-file-access-from-files",
                "--hide-scrollbars",
            ],
        )
        page = browser_instance.new_page(
            viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT},
            device_scale_factor=1,
        )

        for slide_number in range(1, count + 1):
            page.goto(f"{INDEX.as_uri()}?export=1&step=0#slide-{slide_number}", wait_until="networkidle")
            fragments = page.locator(".slide.active .fragment").count()
            for step in range(fragments + 1):
                page.goto(f"{INDEX.as_uri()}?export=1&step={step}#slide-{slide_number}", wait_until="networkidle")
                output = work_dir / f"page-{len(page_images) + 1:03d}-slide-{slide_number:02d}-step-{step:02d}.png"
                page.locator(".slide.active").screenshot(path=str(output))
                page_images.append(output)

        browser_instance.close()
    return page_images


def render_pdf(browser: Path, page_images: list[Path], output: Path, work_dir: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("PDF export requires Python Playwright, which is not installed.") from exc

    image_tags = "\n".join(
        f'<section class="page"><img src="{html.escape(image.as_uri(), quote=True)}" /></section>'
        for image in page_images
    )
    html_path = work_dir / "pdf-pages.html"
    html_path.write_text(
        f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <style>
      @page {{ size: {SLIDE_WIDTH}px {SLIDE_HEIGHT}px; margin: 0; }}
      html, body {{ margin: 0; padding: 0; background: white; }}
      .page {{ width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; page-break-after: always; break-after: page; }}
      .page:last-child {{ page-break-after: auto; break-after: auto; }}
      img {{ display: block; width: {SLIDE_WIDTH}px; height: {SLIDE_HEIGHT}px; }}
    </style>
  </head>
  <body>
    {image_tags}
  </body>
</html>
""",
        encoding="utf-8",
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser_instance = playwright.chromium.launch(
            executable_path=str(browser),
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-gpu-sandbox",
                "--disable-dev-shm-usage",
                "--allow-file-access-from-files",
            ],
        )
        page = browser_instance.new_page(viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(output),
            width=f"{SLIDE_WIDTH}px",
            height=f"{SLIDE_HEIGHT}px",
            print_background=True,
            prefer_css_page_size=True,
        )
        browser_instance.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the HTML slide deck to PDF, expanding fragments into pages.")
    parser.add_argument("--output", type=Path, default=OUT_DIR / "mq_colloquium_2026.pdf")
    parser.add_argument("--keep-images", action="store_true", help="Copy intermediate page PNGs into exports/pdf-pages.")
    args = parser.parse_args()

    browser = find_browser()
    count = slide_count()
    start = time.time()

    with tempfile.TemporaryDirectory(prefix="mq-colloquium-pdf-export-") as tmp:
        work_dir = Path(tmp)
        page_images = capture_pages(browser, count, work_dir)
        render_pdf(browser, page_images, args.output, work_dir)

        if args.keep_images:
            image_dir = OUT_DIR / "pdf-pages"
            image_dir.mkdir(parents=True, exist_ok=True)
            for image in page_images:
                shutil.copy2(image, image_dir / image.name)

    print(f"Exported {count} slides as {len(page_images)} PDF pages to {args.output}")
    print(f"Browser: {browser}")
    print(f"Elapsed: {time.time() - start:.1f}s")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"export:pdf failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
