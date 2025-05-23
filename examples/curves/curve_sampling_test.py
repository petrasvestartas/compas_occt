from compas_occt import _curves
from compas.geometry import Polyline
from compas_viewer import Viewer

print("Testing OCCT NURBS Curve Sampling")

# Sample points from the NURBS curve (50 points by default)
points = _curves.sample_curve_points()
print(f"Sampled {len(points)} points from the NURBS curve")

# Sample with different density
points_high_res = _curves.sample_curve_points(num_points=200)
print(f"Sampled {len(points_high_res)} high-resolution points")

polyline = Polyline(points)
polyline_high_res = Polyline(points_high_res)

viewer = Viewer()
viewer.scene.add(polyline)
viewer.scene.add(polyline_high_res)
viewer.show()
