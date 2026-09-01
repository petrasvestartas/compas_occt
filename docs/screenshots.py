"""Regenerate the example screenshots used in the docs.

Renders every ``docs/examples/**/<name>.py`` offscreen with compas_viewer and writes
``docs/assets/images/example_<name>.jpg``. compas_viewer's own Brep/NURBS scene objects
hard-import ``compas_occ``; we register compas_occt-backed equivalents instead.

Usage (needs ``compas_viewer``)::

    python docs/screenshots.py            # render every example
    python docs/screenshots.py <py> <jpg> # render one example (used internally per subprocess)
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "docs" / "examples"
IMAGES = ROOT / "docs" / "assets" / "images"


def _render_one(example: str, out: str) -> None:
    import runpy

    from compas_viewer import Viewer
    from compas_viewer.scene import register_scene_objects
    from compas_viewer.scene.geometryobject import GeometryObject as ViewerGeometryObject
    from compas_viewer.scene.nurbscurveobject import NurbsCurveObject
    from PySide6 import QtCore

    from compas.colors import Color
    from compas.datastructures import Mesh
    from compas.scene import GeometryObject
    from compas.scene import register
    from compas.scene.descriptors.color import ColorAttribute
    from compas.tolerance import TOL
    from compas_occt.brep import OCCBrep
    from compas_occt.geometry import OCCNurbsCurve
    from compas_occt.geometry import OCCNurbsSurface

    GREY = ColorAttribute(default=Color(0.7, 0.7, 0.7))
    DARK = ColorAttribute(default=Color(0.2, 0.2, 0.2))

    class BrepObject(ViewerGeometryObject, GeometryObject):
        geometry: OCCBrep
        surfacecolor = GREY
        linecolor = DARK

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._viewmesh, self._boundaries = self.geometry.to_tesselation(TOL.lineardeflection)

        @property
        def points(self):
            return self.geometry.points

        @property
        def lines(self):
            lines = []
            for polyline in self._boundaries:
                lines += polyline.lines
            return lines

        @property
        def viewmesh(self):
            return self._viewmesh.to_vertices_and_faces(triangulated=True)

    class SurfaceObject(ViewerGeometryObject, GeometryObject):
        geometry: OCCNurbsSurface
        surfacecolor = GREY
        linecolor = DARK

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            vertices, faces = self.geometry.to_vertices_and_faces(nu=24, nv=24)
            self._mesh = Mesh.from_vertices_and_faces(vertices, faces)

        @property
        def viewmesh(self):
            return self._mesh.to_vertices_and_faces(triangulated=True)

    register_scene_objects()
    register(OCCBrep, BrepObject, context="Viewer")
    register(OCCNurbsCurve, NurbsCurveObject, context="Viewer")
    register(OCCNurbsSurface, SurfaceObject, context="Viewer")

    # several examples call ``viewer.scene.add([...])`` with a list; unpack it
    from compas_viewer.scene.scene import ViewerScene

    _orig_add = ViewerScene.add

    def _add(self, item, **kwargs):
        if isinstance(item, (list, tuple)):
            return [_add(self, sub, **kwargs) for sub in item]
        return _orig_add(self, item, **kwargs)

    ViewerScene.add = _add

    # examples often write to hard-coded paths; make the file writers no-ops for the screenshot
    noop = lambda self, *a, **k: None  # noqa: E731
    for cls in (OCCBrep, OCCNurbsCurve, OCCNurbsSurface):
        for method in ("to_step", "to_iges", "to_stl", "to_brep", "to_obj", "to_json"):
            if hasattr(cls, method):
                setattr(cls, method, noop)

    from compas_viewer.commands import zoom_selected

    orig_show = Viewer.show

    def show(self):
        def grab():
            try:
                import math

                import numpy as np

                zoom_selected(self)  # zoom-extents (the "F" key) -> orientation + target
                cam = self.renderer.camera

                # fit the drawn geometry exactly into the frame (fov + aspect), no cropping
                def drawn_points(o):
                    """The points actually rendered for an object, or its bounding box.

                    Fitting the bounding box of a round object wastes the better part of the
                    frame: the corners of the box stick out well past the silhouette. The
                    vertices that get drawn - the tessellation of a Brep, the points of a
                    polyline - are the silhouette, so prefer those and keep the box as the
                    fallback for anything that does not expose them.
                    """
                    points = list(getattr(o, "points", None) or [])
                    viewmesh = getattr(o, "viewmesh", None)
                    if isinstance(viewmesh, (tuple, list)) and len(viewmesh) == 2:
                        points += list(viewmesh[0] or [])
                    if points:
                        return points
                    box = getattr(o, "bounding_box", None)
                    return list(box) if box is not None else []

                drawn = [point for o in self.scene.objects for point in drawn_points(o)]
                if drawn:
                    pts = np.asarray(drawn, dtype=float).reshape(-1, 3)
                    lo, hi = pts.min(0), pts.max(0)
                    target = (lo + hi) / 2.0
                    to_cam = np.asarray(cam.position, dtype=float) - target
                    to_cam /= np.linalg.norm(to_cam) or 1.0
                    forward = -to_cam
                    up0 = np.array([0.0, 0.0, 1.0]) if abs(forward[2]) < 0.95 else np.array([0.0, 1.0, 0.0])
                    right = np.cross(forward, up0)
                    right /= np.linalg.norm(right) or 1.0
                    up = np.cross(right, forward)
                    rel = pts - target
                    tan_v = math.tan(math.radians(cam.fov) / 2.0)
                    aspect = self.renderer.width() / max(self.renderer.height(), 1)
                    # A point is in frame when |rel . up| <= tan_v * depth, and its depth is
                    # distance + rel . forward. Solving that per point and taking the largest
                    # is what fits them all; maxing the two terms separately (as this used to)
                    # sums the extent of one point with the depth of another, and pushes the
                    # camera much too far back.
                    depth = rel @ forward
                    reach_v = np.abs(rel @ up) / tan_v - depth
                    reach_h = np.abs(rel @ right) / (tan_v * aspect) - depth
                    distance = max(reach_v.max(), reach_h.max()) * 1.05  # margin
                    cam.target = target.tolist()
                    cam.position = (target + to_cam * distance).tolist()
                    self.renderer.update()

                # render double-sided so faces never disappear due to inverted normals
                from OpenGL import GL

                self.renderer.makeCurrent()
                GL.glDisable(GL.GL_CULL_FACE)

                QtCore.QCoreApplication.processEvents()
                self.renderer.grabFramebuffer().save(out, "JPG", 92)
            finally:
                QtCore.QCoreApplication.quit()

        QtCore.QTimer.singleShot(1800, grab)
        orig_show(self)

    Viewer.show = show
    runpy.run_path(example, run_name="__main__")


def _render_all() -> None:
    for example in sorted(EXAMPLES.rglob("*.py")):
        if "__temp" in example.parts:
            continue
        out = IMAGES / ("example_" + example.stem + ".jpg")
        proc = subprocess.run([sys.executable, __file__, str(example), str(out)], capture_output=True)
        ok = out.exists() and proc.returncode == 0
        print(("ok   " if ok else "FAIL ") + str(example.relative_to(EXAMPLES)))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        _render_one(sys.argv[1], sys.argv[2])
    else:
        _render_all()
