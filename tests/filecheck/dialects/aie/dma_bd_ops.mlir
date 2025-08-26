// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP

"builtin.module"() ({
  %0 = memref.alloc() : memref<8xi16>
  %1 = memref.alloc() : memref<32xi8>
  %2 = memref.alloc() : memref<10xi32>
  "aie.dma_bd"(%0) <{bd_id = 7 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
  "aie.dma_bd"(%2) <{bd_id = 8 : i32, len = 10 : i32, offset = 0 : i32}> : (memref<10xi32>) -> ()
  "aie.dma_bd"(%1) <{bd_id = 1 : i32, burst_length = 64 : i32, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
  "aie.dma_bd"(%0) <{bd_id = 0 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
  "aie.dma_bd"(%2) <{bd_id = 1 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<10xi32>) -> ()
  "aie.dma_bd"(%0) <{bd_id = 2 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<8xi16>) -> ()
  "aie.dma_bd"(%1) <{bd_id = 0 : i32, dimensions = #aie<bd_dim_layout_array[<size = 2, stride = 4>, <size = 2, stride = 8>, <size = 4, stride = 1>]>, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
  "aie.dma_bd"(%1) <{bd_id = 0 : i32, dimensions = #aie<bd_dim_layout_array[<size = 2, stride = 4>, <size = 2, stride = 8>, <size = 4, stride = 1>]>, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
  "aie.dma_bd"(%1) <{bd_id = 0 : i32, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
}) : () -> ()


// CHECK-GENERIC:      "builtin.module"() ({
// CHECK-GENERIC-NEXT:   %0 = "memref.alloc"() <{operandSegmentSizes = array<i32: 0, 0>}> : () -> memref<8xi16>
// CHECK-GENERIC-NEXT:   %1 = "memref.alloc"() <{operandSegmentSizes = array<i32: 0, 0>}> : () -> memref<32xi8>
// CHECK-GENERIC-NEXT:   %2 = "memref.alloc"() <{operandSegmentSizes = array<i32: 0, 0>}> : () -> memref<10xi32>
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%0) <{bd_id = 7 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%2) <{bd_id = 8 : i32, len = 10 : i32, offset = 0 : i32}> : (memref<10xi32>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%1) <{bd_id = 1 : i32, burst_length = 64 : i32, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%0) <{bd_id = 0 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%2) <{bd_id = 1 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<10xi32>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%0) <{bd_id = 2 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<8xi16>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%1) <{bd_id = 0 : i32, dimensions = #aie<bd_dim_layout_array[<size = 2, stride = 4>, <size = 2, stride = 8>, <size = 4, stride = 1>]>, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%1) <{bd_id = 0 : i32, dimensions = #aie<bd_dim_layout_array[<size = 2, stride = 4>, <size = 2, stride = 8>, <size = 4, stride = 1>]>, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
// CHECK-GENERIC-NEXT:   "aie.dma_bd"(%1) <{bd_id = 0 : i32, len = 16 : i32, offset = 4 : i32}> : (memref<32xi8>) -> ()
// CHECK-GENERIC-NEXT: }) : () -> ()
