"""Generate a docs page per example and print the mkdocs nav for the Examples section.

For every ``docs/examples/<category>/<name>.py`` that has a rendered
``docs/assets/images/example_<name>.jpg``, write ``docs/examples/<category>/<name>.md`` and
collect a nav entry. Run after ``python docs/screenshots.py``.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "docs" / "examples"
IMAGES = ROOT / "docs" / "assets" / "images"

PAGE = """# {title}

![{title}](../../assets/images/{image})

```python
---8<--- "docs/examples/{category}/{stem}.py"
```
"""


def title_of(stem: str) -> str:
    return " ".join(word.upper() if word in ("aabb", "obb") else word.capitalize() for word in stem.split("_"))


def main() -> int:
    nav: dict[str, list[tuple[str, str]]] = {}
    for example in sorted(EXAMPLES.rglob("*.py")):
        if "__temp" in example.parts:
            continue
        image = "example_" + example.stem + ".jpg"
        if not (IMAGES / image).exists():
            print("skip (no image):", example.stem)
            continue
        category = example.parent.name
        title = title_of(example.stem)
        (example.with_suffix(".md")).write_text(
            PAGE.format(title=title, image=image, category=category, stem=example.stem),
            encoding="utf-8",
        )
        nav.setdefault(category, []).append((title, f"examples/{category}/{example.stem}.md"))

    # print the nav snippet for mkdocs.yml
    print("\n=== NAV (paste under '- Examples:') ===")
    for category in ("breps", "curves", "surfaces"):
        if category not in nav:
            continue
        print(f"      - {category.capitalize()}:")
        for title, path in sorted(nav[category]):
            print(f"          - {title}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
