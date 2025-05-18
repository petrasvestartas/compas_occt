#!/usr/bin/env python3
"""
Test script to verify the integration of the template static library
with the nanobind module.
"""

import compas_occt._primitives as primitives

def test_functions():
    """Test both the local and static library functions"""
    
    # Test the local implementation
    print("\nTesting local 'add' function:")
    result1 = primitives.add(5, 7)
    print(f"5 + 7 = {result1}")
    
    # Test the function that uses the static library
    print("\nTesting static library 'sum_from_static_lib' function:")
    result2 = primitives.sum_from_static_lib(10, 15)
    print(f"10 + 15 = {result2}")
    
    # Verify both implementations produce the same results
    print("\nVerifying that both implementations match:")
    test_a, test_b = 42, 58
    local_result = primitives.add(test_a, test_b)
    static_result = primitives.sum_from_static_lib(test_a, test_b)
    
    print(f"Local add({test_a}, {test_b}) = {local_result}")
    print(f"Static sum_from_static_lib({test_a}, {test_b}) = {static_result}")
    print(f"Results match: {local_result == static_result}")

if __name__ == "__main__":
    print("Testing nanobind module with static library integration")
    test_functions()
