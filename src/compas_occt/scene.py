"""Viewer scene objects for `compas_occt` geometry.

`compas_viewer` only registers a Brep scene object for `compas_occ.OCCBrep`, so a freshly
installed `compas_occt` (without `compas_occ`) has nothing to draw an `OCCBrep` with. This
module ships a `register_scene_objects` plugin -- collected alongside `compas_viewer`'s own --
so that ``viewer.scene.add(occbrep)`` works out of the box.
"""

from compas.plugins import plugin


@plugin(category="factories", requires=["compas_viewer"])
def register_scene_objects():
    from compas_viewer.scene.geometryobject import GeometryObject as ViewerGeometryObject
    from compas_viewer.scene.nurbscurveobject import NurbsCurveObject

    from compas.scene import GeometryObject
    from compas.scene import register
    from compas.tolerance import TOL
    from compas_occt.brep import OCCBrep
    from compas_occt.geometry import OCCNurbsCurve

    class OCCBrepObject(ViewerGeometryObject, GeometryObject):
        """Viewer scene object for displaying a `compas_occt` :class:`OCCBrep`."""

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

    register(OCCBrep, OCCBrepObject, context="Viewer")
    register(OCCNurbsCurve, NurbsCurveObject, context="Viewer")
