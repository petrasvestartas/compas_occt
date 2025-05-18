from compas_occt import _curves


# Get OCCT version
occt_version = _curves.get_occt_version()
print(f"Using OCCT version: {occt_version}")

# Test NURBS curve creation
result = _curves.test_occt_nurbs()
print(result)
