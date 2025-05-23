import time
from compas_viewer import Viewer

# from compas.colors import Color
# from compas.geometry import NurbsSurface
# from compas_occt import NurbsSurface
# from compas.geometry import Point
# from compas.geometry import Polyline

# points = [
#     [Point(0, 0, 0), Point(1, 0, 0), Point(2, 0, 0), Point(3, 0, 0)],
#     [Point(0, 1, 0), Point(1, 1, 2), Point(2, 1, 2), Point(3, 1, 0)],
#     [Point(0, 2, 0), Point(1, 2, 2), Point(2, 2, 2), Point(3, 2, 0)],
#     [Point(0, 3, 0), Point(1, 3, 0), Point(2, 3, 0), Point(3, 3, 0)],
# ]

# # Measure surface creation time
# start_time = time.time()
# surface = NurbsSurface.from_points(points=points)
# surface_creation_time = time.time() - start_time
# print(f"Surface creation time: {surface_creation_time:.4f} seconds")

import numpy as np
from compas.datastructures import Mesh
from compas_occt import _nurbssurface
from compas.geometry import Point, Polyline
from compas.colors import Color
from compas_viewer import Viewer
import time


##################################################################################
# OCCT
##################################################################################



points_array = np.array([
    [0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0],
    [0, 1, 0], [1, 1, 2], [2, 1, 2], [3, 1, 0],
    [0, 2, 0], [1, 2, 2], [2, 2, 2], [3, 2, 0],
    [0, 3, 0], [1, 3, 0], [2, 3, 0], [3, 3, 0]
])

start_time = time.time()
surface = _nurbssurface.create_nurbs_surface_from_points(points_array, 4, 4, 3, 3)
print("OCCT surface creation time: ", time.time() - start_time)

start_time = time.time()
control_points = _nurbssurface.get_control_points(surface)
print("OCCT control points extraction time: ", time.time() - start_time)

start_time = time.time()
mesh = Mesh.from_vertices_and_faces(*_nurbssurface.get_mesh(surface, 0.01))
print("COMPAS mesh creation time: ", time.time() - start_time)

start_time = time.time()
u_isocurves = _nurbssurface.get_isocurves(surface, True, 7, 25)
v_isocurves = _nurbssurface.get_isocurves(surface, False, 7, 25)
print("OCCT isocurve extraction time: ", time.time() - start_time)

##################################################################################
# Viewer
##################################################################################

viewer = Viewer()

# Mesh
viewer.scene.add(mesh, show_lines=False)

# Control points
control_point_objects = [Point(cp[0], cp[1], cp[2]) for cp in control_points]
viewer.scene.add(control_point_objects, pointsize=10)

# Cage Polylines
grid_points = points_array.reshape(4, 4, 3).tolist()
grid_polylines = [Polyline(row) for row in grid_points] + [Polyline(col) for col in zip(*grid_points)]
viewer.scene.add(grid_polylines, linewidth=1)

# Isocurves
all_isocurves = [Polyline([[p[0], p[1], p[2]] for p in curve]) for curve in u_isocurves + v_isocurves]
viewer.scene.add(all_isocurves, linewidth=4, color=(0.75, 0.75, 0.75))

viewer.show()
