// RUN: XDSL_ROUNDTRIP
// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP


%0 = aie.tile (1, 2)
%1 = aie.core(%0) {
  %c0 = arith.constant 0 : index
  aie.end
}

// CHECK:      %{{.*}} = aie.tile(1, 2)
// CHECK-NEXT: %{{.*}} = aie.core(%{{.*}}) {
// CHECK-NEXT:   %{{.*}} = arith.constant 0 : index
// CHECK-NEXT:   aie.end
// CHECK-NEXT: }

// CHECK-GENERIC:      "builtin.module"() ({
// CHECK-GENERIC-NEXT:   %{{.*}} = "aie.tile"() <{{{["]?}}col{{["]?}} = 1 : i32, {{["]?}}row{{["]?}} = 2 : i32}> : () -> index
// CHECK-GENERIC-NEXT:   %{{.*}} = "aie.core"(%{{.*}}) <{{{["]?}}stack_size{{["]?}} = 1024 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 0 : index}> : () -> index
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : (index) -> index
// CHECK-GENERIC-NEXT: }) : () -> ()
