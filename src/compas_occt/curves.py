import compas_occt._curves as curves

# Get OCCT version
print(curves.get_occt_version())

# Run the full NURBS test
result = curves.test_occt_nurbs()
print(result)