from pathlib import Path
from compas_occt import Point

# Create a point and export to STEP
pt = Point(1.0, 2.0, 3.0)
print(f"Created: {pt}")

# Export with name, color, and attributes
output_file = Path(__file__).parent.parent / "data" / "my_point.step"
success = pt.to_step(output_file, 
                     name="MyPoint", 
                     color=[0.0, 1.0, 0.0],  # Green
                     attributes={"material": "steel", "weight": "0.1kg"})

print(f"Exported to {output_file}: {'Success' if success else 'Failed'}")
