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


aiex.runtime_sequence (%4 : memref<4096xi8>) {

// CHECK-NEXT: aiex.runtime_sequence(%{{.*}} : memref<4096xi8>) {
// CHECK-GENERIC-NEXT: "aiex.runtime_sequence"() ({
// CHECK-GENERIC-NEXT: ^2(%{{.*}} : memref<4096xi8>):

aiex.npu.dma_memcpy_nd(0, 0, %4[0, 0, 0, 0][1, 1, 1, 4096][0, 0, 0, 1]) {id = 2 : i64, issue_token = true, metadata = @test} : memref<4096xi8>

// CHECK-NEXT: aiex.npu.dma_memcpy_nd(0, 0, %{{.*}}[0, 0, 0, 0][1, 1, 1, 4096][0, 0, 0, 1]) {id = 2 : i64, issue_token = true, metadata = @test} : memref<4096xi8>

// CHECK-GENERIC-NEXT: "aiex.npu.dma_memcpy_nd"(%{{.*}}) <{
// CHECK-GENERIC-SAME: id = 2 : i64
// CHECK-GENERIC-SAME: issue_token = true
// CHECK-GENERIC-SAME: metadata = @test
// CHECK-GENERIC-SAME: static_offsets = array<i64: 0, 0, 0, 0> 
// CHECK-GENERIC-SAME: static_sizes = array<i64: 1, 1, 1, 4096> 
// CHECK-GENERIC-SAME: static_strides = array<i64: 0, 0, 0, 1>
// CHECK-GENERIC-SAME: x = 0 : i64
// CHECK-GENERIC-SAME: y = 0 : i64 
// CHECK-GENERIC-SAME: }> : (memref<4096xi8>) -> ()

}

}
