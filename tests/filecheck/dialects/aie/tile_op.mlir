// RUN: XDSL_ROUNDTRIP
// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP


%0 = aie.tile (1, 2)

// CHECK: %{{.*}} = aie.tile(1, 2)
// CHECK-GENERIC:   %{{.*}} = "aie.tile"() <{{{["]?}}col{{["]?}} = 1 : i32, {{["]?}}row{{["]?}} = 2 : i32}> : () -> index

