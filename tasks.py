from __future__ import print_function

import os

from compas_invocations2 import build
from compas_invocations2 import style
from compas_invocations2 import tests
from invoke import Collection
from invoke import task


@task
def docs(ctx):
    """Build the documentation site with mkdocs."""
    with ctx.cd(os.path.dirname(__file__)):
        ctx.run("mkdocs build")


@task
def docs_serve(ctx):
    """Serve the documentation locally with mkdocs (live reload)."""
    with ctx.cd(os.path.dirname(__file__)):
        ctx.run("mkdocs serve")


# This project documents with mkdocs only -- the sphinx-based docs/linkcheck tasks from
# compas_invocations2 are intentionally not registered.
ns = Collection(
    style.check,
    style.lint,
    style.format,
    docs,
    docs_serve,
    tests.test,
    tests.testdocs,
    tests.testcodeblocks,
    build.prepare_changelog,
    build.clean,
    build.release,
    build.build_ghuser_components,
)
ns.configure(
    {
        "base_folder": os.path.dirname(__file__),
        "ghuser": {
            "source_dir": "src/compas_occt_ghpython/components",
            "target_dir": "src/compas_occt_ghpython/components/ghuser",
            "prefix": "compas_occt: ",
        },
    }
)
