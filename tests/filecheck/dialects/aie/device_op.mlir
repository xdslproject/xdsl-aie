// RUN: XDSL_ROUNDTRIP
// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP

// operation: aie.device

aie.device(xcvc1902) {
	arith.constant 1 : i32
}

aie.device(xcve2302) {
	arith.constant 1 : i32
}

aie.device(xcve2802) {
	arith.constant 1 : i32
}

aie.device(npu1) {
	arith.constant 1 : i32
}

aie.device(npu1_1col) {
	arith.constant 1 : i32
}

aie.device(npu1_2col) {
	arith.constant 1 : i32
}

aie.device(npu1_3col) {
	arith.constant 1 : i32
}

aie.device(npu1_4col) {
	arith.constant 1 : i32
}

aie.device(npu2) {
	arith.constant 1 : i32
}

// CHECK:      module {
// CHECK-NEXT:   aie.device(xcvc1902) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(xcve2302) {
// CHECK-NEXT:     %{{.*}}  = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(xcve2802) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(npu1) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(npu1_1col) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(npu1_2col) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(npu1_3col) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(npu1_4col) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT:   aie.device(npu2) {
// CHECK-NEXT:     %{{.*}} = arith.constant 1 : i32
// CHECK-NEXT:   }
// CHECK-NEXT: }

// CHECK-GENERIC:      "builtin.module"() ({
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 1 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 2 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 3 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 4 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 5 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 6 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 7 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 8 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT:   "aie.device"() <{{{["]?}}device{{["]?}} = 9 : i32}> ({
// CHECK-GENERIC-NEXT:     %{{.*}} = "arith.constant"() <{{{["]?}}value{{["]?}} = 1 : i32}> : () -> i32
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT: }) : () -> ()
