from typing import Optional

from compas.geometry import CurveType
from compas.geometry import SurfaceType
from compas_occt import _occt as _brep
from compas_occt import conversions

from .brep import OCCBrep


class OCCBrepBuilder:
    """Class for building OCC Breps from serialisation data.

    Parameters
    ----------
    make_solid : bool, optional
    """

    def __init__(self, make_solid: Optional[bool] = True):
        self.make_solid = make_solid

    def build(self, faces: list[dict]) -> OCCBrep:
        """Build a COMPAS OCC brep from list of faces represented by their serialisation data.

        Parameters
        ----------
        faces : list[dict]
            A list of faces represented by their serialisation data.

        Returns
        -------
        :class:`OCCBrep`

        """
        occ_faces = []
        for facedata in faces:
            occ_faces.append(self.build_face(facedata))

        shell = _brep.shell_from_faces(occ_faces)
        brep = OCCBrep.from_native(shell)
        brep.heal()
        if self.make_solid:
            brep.make_solid()
        return brep

    def build_edge(self, edgedata: dict):
        """Build an OCC edge from edge serialisation data with 3D curve geometry.

        Parameters
        ----------
        edgedata : dict
            The serialisation data representing an edge.

        Returns
        -------
        Shape

        """
        start = conversions.point_to_occ(edgedata["start"])
        end = conversions.point_to_occ(edgedata["end"])
        u, v = edgedata["domain"]

        if edgedata["type"] == CurveType.LINE:
            return _brep.make_edge_line(conversions.line_to_occ(edgedata["curve"]), points=(start, end))

        elif edgedata["type"] == CurveType.CIRCLE:
            curve = _brep.geom_circle(conversions.circle_to_occ(edgedata["curve"]))
            return _brep.make_edge_curve(curve, params=(u, v), points=(start, end))

        elif edgedata["type"] == CurveType.ELLIPSE:
            curve = _brep.geom_ellipse(conversions.ellipse_to_occ(edgedata["curve"]))
            return _brep.make_edge_curve(curve, params=(u, v), points=(start, end))

        elif edgedata["type"] == CurveType.BSPLINE:
            curve = edgedata["curve"].native_curve
            return _brep.make_edge_curve(curve, params=(u, v), points=(start, end))

        else:
            raise NotImplementedError

    def build_edge2d(self, edgedata, surface):
        """Build an OCC edge from edge serialisation data with 2D curve geometry embedded on a surface.

        Parameters
        ----------
        edgedata : dict
            The serialisation data representing an edge.

        Returns
        -------
        Shape

        """
        raise NotImplementedError

    def build_wire(self, edges: list[dict], surface):
        """Build an OCC wire from a list of edges represented by their serialisation data.

        Parameters
        ----------
        edges : list[dict]
            The serialisation data of the edges.
        surface : GeomSurface
            The surface geometry of the face of the wire.

        Returns
        -------
        Shape

        """
        occ_edges = []
        for edgedata in edges:
            if edgedata["dimension"] == 2:
                edge = self.build_edge2d(edgedata, surface)
            else:
                edge = self.build_edge(edgedata)

            if edgedata["orientation"] != _brep.shape_orientation(edge):
                edge = _brep.set_orientation(edge, edgedata["orientation"])

            occ_edges.append(edge)

        return _brep.make_wire(occ_edges)

    def build_face(self, data):
        """Build an OCC face from face serialisation data.

        Parameters
        ----------
        data : dict
            The serialisation data of the face.

        Returns
        -------
        Shape

        """
        if data["type"] == SurfaceType.PLANE:
            surface = _brep.geom_plane(conversions.plane_to_occ(data["surface"]))

        elif data["type"] == SurfaceType.CYLINDER:
            surface = _brep.geom_cylinder(conversions.cylinder_to_occ(data["surface"]))

        elif data["type"] == SurfaceType.SPHERE:
            surface = _brep.geom_sphere(conversions.sphere_to_occ(data["surface"]))

        elif data["type"] == SurfaceType.BSPLINE_SURFACE:
            surface = data["surface"].native_surface

        else:
            raise NotImplementedError

        loops = data["loops"]
        boundary = self.build_wire(loops[0], surface)
        face = _brep.make_face_surface(surface, loop=boundary)

        if len(loops) > 1:
            for edges in loops[1:]:
                hole = self.build_wire(edges, surface)
                face = _brep.face_add_loop(face, hole, False)

        if data["orientation"] != _brep.shape_orientation(face):
            face = _brep.set_orientation(face, data["orientation"])

        if not _brep.is_valid(face):
            face = _brep.fix_face(face)

        return face
