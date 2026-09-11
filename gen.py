#!/usr/bin/env python3
"""Generate README.md from greatness.csv using only the Python standard library."""

import argparse
import csv
from pathlib import Path


COLUMNS = ["category", "title", "url", "author1", "year1", "author2", "year2"]
INTRO = (
    "# Greatness\n\n"
    "> Greatness awaits. \u2014 Sony\n\n"
    "This repo lists my favorite works in various fields."
)
APPROXIMATE_YEAR_NOTE = (
    "> [!NOTE]  \n"
    "> The original release date of this model cannot be verified."
)


def render_readme(source: Path) -> str:
    sections = [INTRO]
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        if next(reader, None) != COLUMNS:
            raise ValueError(f"Expected CSV header: {','.join(COLUMNS)}")

        for row in reader:
            if not row:
                continue
            if len(row) != len(COLUMNS):
                raise ValueError(f"CSV line {reader.line_num}: expected 7 columns")
            category, title, url, author1, year1, author2, year2 = (
                value.strip() for value in row
            )
            if not all((category, title, author1, year1)):
                raise ValueError(
                    f"CSV line {reader.line_num}: category, title, author1 and year1 "
                    "must not be empty"
                )
            if bool(author2) != bool(year2):
                raise ValueError(
                    f"CSV line {reader.line_num}: author2 and year2 must be supplied together"
                )

            heading = f"### {title}"
            if url:
                heading += f" [\u2197]({url})"
            blocks = [f"## {category}", heading, f"{author1}  \n{year1}"]
            if author2:
                blocks.append(f"{author2}  \n{year2}")
            if any(year.startswith("c.") for year in (year1, year2)):
                blocks.append(APPROXIMATE_YEAR_NOTE)
            sections.append("\n\n".join(blocks))

    if len(sections) == 1:
        raise ValueError("CSV contains no entries")
    return "\n\n<br>\n\n".join(sections) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source", nargs="?", type=Path, default=root / "greatness.csv",
        help="Input CSV (default: greatness.csv beside this script)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=root / "README.md",
        help="Output Markdown (default: README.md beside this script)",
    )
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("Input and output must be different files")
    try:
        markdown = render_readme(args.source)
        args.output.write_text(markdown, encoding="utf-8")
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
