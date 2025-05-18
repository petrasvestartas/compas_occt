
from compas_occt import _primitives


print("Testing COMPAS OCCT integration")

# Test basic functions from the module
result = _primitives.add(5, 7)
print(f"Regular add function: 5 + 7 = {result}")

# Test OCCT point creation function
point_coords = _primitives.create_point(1.0, 2.0, 3.0)
print(f"OCCT created point: {point_coords}")

# Test OCCT linking
occt_info = _primitives.test_occt_linking()
print(f"OCCT integration test: {occt_info}")

# Test NURBS curve sampling
print("Testing NURBS curve sampling...")
points = _primitives.sample_nurbs_curve(10)
print(f"NURBS curve with {len(points)} points")
