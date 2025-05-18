#include "compas.h"

// Include the static library's header
#include "calculator.h"

// Define our own function using regular C++
int add(int a, int b) {
    return a + b;
}

// This function uses the static library's implementation
int sum_from_static_lib(int a, int b) {
    // Call the function from the static library
    return math::sum(a, b);
}

NB_MODULE(_primitives, m) {
    m.doc() = "Primitives example with static library integration.";

    // Expose our regular function
    m.def("add", &add, "a"_a, "b"_a=1, "Add two numbers using local implementation");
    
    // Expose the function that uses the static library
    m.def("sum_from_static_lib", &sum_from_static_lib, "a"_a, "b"_a=1, 
          "Add two numbers using the template static library implementation");
}
