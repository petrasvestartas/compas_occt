import os
from compas_occt import _step

_step.tutorial()

# # Get the directory of this script
# script_dir = os.path.dirname(os.path.abspath(__file__))

# # Define cross-platform paths
# input_path = os.path.join(script_dir, "..", "..", "data", "brep.step")
# output_path = os.path.join(script_dir, "..", "..", "data", "brep_assembly.step")

# # Normalize paths for the current OS
# input_path = os.path.normpath(input_path)
# output_path = os.path.normpath(output_path)

# print("=== OCCT Assembly Creation Example ===")
# print(f"Reading STEP file from: {input_path}")
# print(f"Creating assembly with attributes...")
# print(f"Writing assembly STEP file to: {output_path}")
# print()
# print("Assembly features:")
# print("- 4 translated copies of the original shape")
# print("- Named components: 'Original Screw', 'Screw Copy 1', etc.")
# print("- Color attributes: Red, Green, Blue, Yellow")
# print("- Validation properties: Volume calculations included in names")
# print("- Proper assembly structure using XDE framework")
# print()

# _step.assemble(input_path, output_path)

# print("Assembly creation completed successfully!")
# print(f"Open '{output_path}' in a CAD viewer to see the assembly with attributes.")
