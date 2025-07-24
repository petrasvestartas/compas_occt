from compas.geometry import Box
from compas.geometry import Frame
from pathlib import Path
from compas.datastructures import Tree
from compas.datastructures import TreeNode
from compas_occt import _step


# STEP files for components (root will be pure assembly)
branch0_filepath = Path(__file__).parent.parent.parent / "data" / "box1.step"
Box(1,1,1, Frame([-1,0,-1], [1,0,0], [0,1,0])).to_brep().to_step(branch0_filepath)

branch1_filepath = Path(__file__).parent.parent.parent / "data" / "box2.step"
Box(1,1,1, Frame([1,0,-1], [1,0,0], [0,1,0])).to_brep().to_step(branch1_filepath)

branch10_filepath = Path(__file__).parent.parent.parent / "data" / "box3.step"
Box(1,1,1, Frame([2,0,-2], [1,0,0], [0,1,0])).to_brep().to_step(branch10_filepath)

# Tree with pure assembly root (no geometry)
tree = Tree()
root = TreeNode("root", **{"my_root_attribute0": "a", "my_root_attribute1": "b"})
branch0 = TreeNode("branch0", **{"step": str(branch0_filepath), "my_branch_attribute00": "0a", "my_branch_attribute01": "0b"})
branch1 = TreeNode("branch1", **{"step": str(branch1_filepath), "my_branch_attribute10": "1a", "my_branch_attribute11": "1b"})
branch10 = TreeNode("branch10", **{"step": str(branch10_filepath), "my_branch_attribute0": "1a", "my_branch_attribute1": "1"})
tree.add(root)
root.add(branch0)
root.add(branch1)
branch1.add(branch10)

# Serialize
tree_filepath = Path(__file__).parent.parent.parent / "data" / "tree.json"
tree.to_json(tree_filepath)

# Call OpenCascade function to convert json to a step file
step_filepath = Path(__file__).parent.parent.parent / "data" / "assembly.step"
_step.from_json(str(tree_filepath), str(step_filepath))



