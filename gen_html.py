#!/usr/bin/env python3
"""Generate index.html as a scrolling-credits webpage from greatness.csv."""

import argparse
import csv
import html
import re
from pathlib import Path


COLUMNS = ["category", "title", "url", "author1", "year1", "author2", "year2"]
ITALIC_TEXT = re.compile(r"_([^_]+)_")


def read_entries(source: Path) -> list[dict[str, str]]:
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"Expected CSV header: {','.join(COLUMNS)}")

        entries = []
        for row in reader:
            entry = {key: (value or "").strip() for key, value in row.items()}
            if not all(entry[key] for key in ("category", "title", "author1", "year1")):
                raise ValueError(
                    f"CSV line {reader.line_num}: category, title, author1 and year1 "
                    "must not be empty"
                )
            if bool(entry["author2"]) != bool(entry["year2"]):
                raise ValueError(
                    f"CSV line {reader.line_num}: author2 and year2 must be supplied together"
                )
            entries.append(entry)

    if not entries:
        raise ValueError("CSV contains no entries")
    return entries


def render_text(value: str) -> str:
    escaped = html.escape(value)
    return ITALIC_TEXT.sub(r"<em>\1</em>", escaped)


def render_item(entry: dict[str, str]) -> str:
    category = render_text(entry["category"])
    title = render_text(entry["title"])
    author1 = render_text(entry["author1"])
    year1 = render_text(entry["year1"])

    if entry["url"]:
        url = html.escape(entry["url"], quote=True)
        title = f'<a href="{url}">{title}</a>'

    credits = [f"      <p>{author1}<br>{year1}</p>"]
    if entry["author2"]:
        author2 = render_text(entry["author2"])
        year2 = render_text(entry["year2"])
        credits.append(f"      <p>{author2}<br>{year2}</p>")
    credit_html = "\n".join(credits)

    return (
        "    <section>\n"
        f"      <p>{category}</p>\n"
        f'      <h2 lang="zh-Hant">{title}</h2>\n'
        f"{credit_html}\n"
        "    </section>"
    )


def render_page(entries: list[dict[str, str]]) -> str:
    items = "\n".join(render_item(entry) for entry in entries)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#000000">
  <meta name="color-scheme" content="dark">
  <title>Greatness</title>
  <style>
    * {{ box-sizing: border-box; }}

    html {{
      font-size: clamp(16px, 1.5vw, 32px);
    }}

    html,
    body {{
      width: 100%;
      height: 100%;
      margin: 0;
      background: #000;
      color: #fff;
    }}

    body {{
      font-family: "Kusa", "Gill Sans", "Gill Sans MT", sans-serif;
      width: 85vw;
      margin: 0 auto;
      padding: 50vh 0 0;
      text-align: center;
    }}

    section {{
      margin: 0 0 15vh;
    }}

    section > p:first-child {{
      margin: 0 0 1rem;
      font-size: 0.75rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
    }}

    h2 {{
      font-size: 1.5rem;
      font-weight: 600;
    }}

    section > p:not(:first-child) {{
      font-size: 1rem;
      line-height: 1.5;
    }}

    a {{
      color: inherit;
      text-decoration: none;
    }}

    em {{
      font-style: italic;
    }}

    footer {{
      display: grid;
      height: 100vh;
      place-items: center;
    }}

    footer img {{
      width: 4rem;
      height: auto;
      filter: invert(1);
    }}

    @font-face {{
      font-family: "Kusa";
      font-weight: 400 700;
      src: local("Gill Sans MT"), local("Gill Sans");
      size-adjust: 110%;
      unicode-range: U+0000-00FF;
    }}

    @font-face {{
      font-family: "Kusa";
      font-weight: 400 700;
      src: local("Helvetica"), local("Arial");
      unicode-range: U+0100-2009, U+2020-10FFFF;
    }}
  </style>
</head>
<body>
{items}
  <footer>
    <a href=".."><img src="../images/logo.svg" alt="Kusa"></a>
  </footer>
  <script>
    const AUTO_SCROLL_SPEED = 32;
    const IDLE_DELAY = 1800;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const scrollKeys = new Set([
      "ArrowDown", "ArrowUp", "PageDown", "PageUp", "Home", "End", " ",
    ]);

    let resumeAt = 0;
    let previousTime = performance.now();
    let scrollPosition = window.scrollY;
    let pointerIsDown = false;

    function pauseAutoScroll() {{
      resumeAt = performance.now() + IDLE_DELAY;
      scrollPosition = window.scrollY;
    }}

    window.addEventListener("wheel", pauseAutoScroll, {{ passive: true }});
    window.addEventListener("touchstart", pauseAutoScroll, {{ passive: true }});
    window.addEventListener("touchmove", pauseAutoScroll, {{ passive: true }});
    window.addEventListener("pointerdown", () => {{
      pointerIsDown = true;
      pauseAutoScroll();
    }});
    window.addEventListener("pointermove", () => {{
      if (pointerIsDown) pauseAutoScroll();
    }});
    window.addEventListener("pointerup", () => {{
      pointerIsDown = false;
      pauseAutoScroll();
    }});
    window.addEventListener("keydown", (event) => {{
      if (scrollKeys.has(event.key)) pauseAutoScroll();
    }});

    function autoScroll(time) {{
      const elapsed = Math.min(time - previousTime, 50);
      previousTime = time;

      if (!reducedMotion.matches && !pointerIsDown && time >= resumeAt) {{
        const maximum = document.documentElement.scrollHeight - window.innerHeight;
        if (window.scrollY >= maximum - 1) {{
          window.scrollTo(0, maximum);
          return;
        }} else {{
          scrollPosition += (AUTO_SCROLL_SPEED * elapsed) / 1000;
          window.scrollTo(0, scrollPosition);
        }}
      }} else {{
        scrollPosition = window.scrollY;
      }}

      requestAnimationFrame(autoScroll);
    }}

    requestAnimationFrame(autoScroll);
  </script>
</body>
</html>
"""


def main() -> None:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=root / "greatness.csv",
        help="Input CSV (default: greatness.csv beside this script)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=root / "index.html",
        help="Output HTML (default: index.html beside this script)",
    )
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("Input and output must be different files")

    try:
        page = render_page(read_entries(args.source))
        args.output.write_text(page, encoding="utf-8")
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
