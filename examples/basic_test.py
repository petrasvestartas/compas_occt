#!/usr/bin/env python

# Import our module
from compas_occt import _primitives

def main():
    print("Testing COMPAS OCCT integration")
    
    # Test basic functions from the module
    result = _primitives.add(5, 7)
    print(f"Regular add function: 5 + 7 = {result}")
    
    result = _primitives.sum_from_static_lib(5, 7)
    print(f"Static library add function: 5 + 7 = {result}")
    
if __name__ == "__main__":
    main()
