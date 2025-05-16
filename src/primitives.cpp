#include "compas.h"

int add(int a, int b) {
    return a + b;
}

NB_MODULE(_primitives, m) {
    m.doc() = "Primitives example.";

    m.def("add", &add, "a"_a, "b"_a=1, "Add two numbers");
}
