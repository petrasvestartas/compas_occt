"""Smoke-test every docs example on the current OS, headless.

Strips the GUI (``compas_viewer``) from each example and executes the remaining
geometry/kernel code. This verifies the examples actually run against the
installed ``compas_occt`` wheel on Linux / macOS / Windows -- something the unit
tests do not cover (the examples end in ``viewer.show()``, which needs a display).

Examples that still use the old pythonocc ``OCC.Core`` API are reported as SKIP
(they were never ported to compas_occt). Exit code is non-zero if any runnable
example raises.

Usage:  python tests/run_examples_headless.py
"""

import ast
import contextlib
import io
import os
import pathlib
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "docs" / "examples"


def uses_pythonocc(src):
    for node in ast.parse(src).body:
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "OCC":
            return True
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "OCC" for a in node.names):
            return True
    return False


def strip_viewer(src):
    tree = ast.parse(src)
    keep = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            names = " ".join(a.name for a in node.names)
            if "compas_viewer" in (mod + " " + names):
                continue
        seg = ast.get_source_segment(src, node) or ""
        if "Viewer" in seg or "viewer" in seg:
            continue
        keep.append(node)
    return compile(ast.Module(body=keep, type_ignores=[]), "<stripped>", "exec")


def run_one(path):
    code = strip_viewer(path.read_text(encoding="utf-8"))
    g = {"__name__": "__main__", "__file__": str(path)}
    cwd = os.getcwd()
    os.chdir(path.parent)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(code, g)
    finally:
        os.chdir(cwd)


def main():
    import compas_occt

    print(f"compas_occt {compas_occt.__version__} on {sys.platform} / Python {sys.version.split()[0]}\n")

    files = sorted(p for p in EXAMPLES.rglob("*.py") if "__temp" not in p.parts)
    passed, failed, skipped = [], [], []
    for f in files:
        rel = f.relative_to(EXAMPLES).as_posix()
        src = f.read_text(encoding="utf-8")
        if uses_pythonocc(src):
            skipped.append(rel)
            print(f"SKIP  {rel}  (uses pythonocc OCC.Core)")
            continue
        try:
            run_one(f)
            passed.append(rel)
            print(f"PASS  {rel}")
        except Exception:
            err = traceback.format_exc().strip().splitlines()[-1][:160]
            failed.append((rel, err))
            print(f"FAIL  {rel}  -> {err}")

    print("\n==================== SUMMARY ====================")
    print(f"  passed:  {len(passed)}")
    print(f"  failed:  {len(failed)}")
    print(f"  skipped: {len(skipped)} (pythonocc, not ported)")
    print(f"  total:   {len(files)}")
    if failed:
        print("\nFAILURES:")
        for rel, err in failed:
            print(f"  {rel}\n      {err}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
