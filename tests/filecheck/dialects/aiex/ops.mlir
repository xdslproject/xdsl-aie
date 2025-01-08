// RUN: XDSL_ROUNDTRIP
// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP



aie.device(npu1_1col) {
// CHECK: aie.device
// CHECK-GENERIC: "aie.device"

aiex.runtime_sequence () { }

// CHECK-NEXT: aiex.runtime_sequence() {
// CHECK-NEXT: }

// CHECK-GENERIC-NEXT: "aiex.runtime_sequence"() ({
// CHECK-GENERIC-NEXT: }) : () -> ()

aiex.runtime_sequence(%0 : memref<16xi8>, %1 : memref<16xi8>) { }

// CHECK-NEXT: aiex.runtime_sequence(%{{.*}}: memref<16xi8>, %{{.*}}: memref<16xi8>) {
// CHECK-NEXT: }

// CHECK-GENERIC-NEXT: "aiex.runtime_sequence"() ({
// CHECK-GENERIC-NEXT: ^{{.*}}(%{{.*}}: memref<16xi8>, %{{.*}}: memref<16xi8>):
// CHECK-GENERIC-NEXT: }) : () -> ()

aiex.runtime_sequence @testabc(%2 : memref<16xi8>, %3 : memref<16xi8>) { }

// CHECK-NEXT: aiex.runtime_sequence @testabc(%{{.*}}: memref<16xi8>, %{{.*}}: memref<16xi8>) {
// CHECK-NEXT: }

// CHECK-GENERIC-NEXT: "aiex.runtime_sequence"() <{sym_name = "testabc"}> ({
// CHECK-GENERIC-NEXT: ^{{.*}}(%{{.*}}: memref<16xi8>, %{{.*}}: memref<16xi8>):
// CHECK-GENERIC-NEXT: }) : () -> ()

}
