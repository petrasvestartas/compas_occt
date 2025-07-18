#include <iostream>
#include <BRepLib_MakeShape.hxx>
#include <TopoDS_Shape.hxx>

int main() {
    std::cout << "Testing BRepLib_MakeShape RTTI" << std::endl;
    // Just create a reference to the class to force RTTI to be used
    BRepLib_MakeShape* shape = nullptr;
    std::cout << "BRepLib_MakeShape reference created" << std::endl;
    return 0;
}
