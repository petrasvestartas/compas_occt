"""Patch the installed `compas_viewer` for Python 3.14.

`compas_viewer` 2.0.2 (the current PyPI release, and `main` at the time of writing) reads
``self.__annotations__`` inside its dataclass ``Config.__post_init__``. On Python 3.14
(PEP 749) instance access to ``__annotations__`` no longer falls back to the class for
dataclass instances, so creating a ``Viewer`` raises::

    AttributeError: 'MenubarConfig' object has no attribute '__annotations__'

This is an upstream `compas_viewer` bug, not a `compas_occt` one. The one-line fix is to read
the annotations from the class (``type(self).__annotations__``). Run this once after installing
`compas_viewer` (e.g. ``python tools/patch_compas_viewer.py``); it is idempotent and a no-op on
Python < 3.14 / once already patched.
"""

import pathlib

import compas_viewer

OLD = "self.__annotations__[field_name]"
NEW = "type(self).__annotations__[field_name]"


def main() -> int:
    config = pathlib.Path(compas_viewer.__file__).parent / "config.py"
    text = config.read_text(encoding="utf-8")
    if NEW in text:
        print(f"compas_viewer already patched: {config}")
        return 0
    if OLD not in text:
        print(f"nothing to patch (unexpected compas_viewer version): {config}")
        return 0
    config.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print(f"patched compas_viewer for Python 3.14: {config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
