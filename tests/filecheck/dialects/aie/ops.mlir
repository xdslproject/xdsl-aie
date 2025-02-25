// RUN: XDSL_ROUNDTRIP
// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP

aie.device(npu1) {


// CHECK:      module {
// CHECK-NEXT:   aie.device(npu1) {

// CHECK-GENERIC:      "builtin.module"() ({
// CHECK-GENERIC-NEXT:   "aie.device"() <{device = 4 : i32}> ({


%1 = aie.tile(0, 1)
%2 = aie.tile(0, 2)
%21 = aie.tile(0, 3)


// CHECK-NEXT:     %{{.*}} = aie.tile(0, 1)
// CHECK-NEXT:     %{{.*}} = aie.tile(0, 2)
// CHECK-NEXT:     %{{.*}} = aie.tile(0, 3)


// CHECK-GENERIC-NEXT:     %{{.*}} = "aie.tile"() <{col = 0 : i32, row = 1 : i32}> : () -> index
// CHECK-GENERIC-NEXT:     %{{.*}} = "aie.tile"() <{col = 0 : i32, row = 2 : i32}> : () -> index
// CHECK-GENERIC-NEXT:     %{{.*}} = "aie.tile"() <{col = 0 : i32, row = 3 : i32}> : () -> index


aie.objectfifo @of1 (%1, { %2 }, 4 : i32) : !aie.objectfifo<memref<16xi32>>

// CHECK-NEXT:     aie.objectfifo @of1(%{{.*}}, {%{{.*}}}, 4 : i32) : !aie.objectfifo<memref<16xi32>>
// CHECK-GENERIC-NEXT:     "aie.objectfifo"(%{{.*}}, %{{.*}}) <{dimensionsFromStreamPerConsumer = #aie<bd_dim_layout_array_array[[]]>, dimensionsToStream = #aie<bd_dim_layout_array[]>, disable_synchronization = false, elemNumber = 4 : i32, elemType = !aie.objectfifo<memref<16xi32>>, plio = false, sym_name = "of1", via_DMA = false}> : (index, index) -> ()

aie.objectfifo @of2 (%2, { %21 }, 4 : i32) : !aie.objectfifo<memref<16xi32>>

// CHECK-NEXT:     aie.objectfifo @of2(%{{.*}}, {%{{.*}}}, 4 : i32) : !aie.objectfifo<memref<16xi32>>
// CHECK-GENERIC-NEXT:     "aie.objectfifo"(%{{.*}}, %{{.*}}) <{dimensionsFromStreamPerConsumer = #aie<bd_dim_layout_array_array[[]]>, dimensionsToStream = #aie<bd_dim_layout_array[]>, disable_synchronization = false, elemNumber = 4 : i32, elemType = !aie.objectfifo<memref<16xi32>>, plio = false, sym_name = "of2", via_DMA = false}> : (index, index) -> ()

aie.objectfifo.link [@of1] -> [@of2] ([] [])

// CHECK-NEXT: aie.objectfifo.link [@of1] -> [@of2]([] [])
// CHECK-GENERIC-NEXT: "aie.objectfifo.link"() <{dst_offsets = [], fifoIns = [@of1], fifoOuts = [@of2], src_offsets = []}> : () -> ()

%3 = aie.core(%2) {

// CHECK-NEXT: %{{.*}} = aie.core(%{{.*}}) {
// CHECK-GENERIC-NEXT: %{{.*}} = "aie.core"(%{{.*}}) <{stack_size = 1024 : i32}> ({

%4 = aie.objectfifo.acquire @of1(Consume, 1) : !aie.objectfifosubview<memref<16xi32>>

// CHECK-NEXT: %{{.*}} = aie.objectfifo.acquire @of1(Consume, 1) : !aie.objectfifosubview<memref<16xi32>>
// CHECK-GENERIC-NEXT: %{{.*}} = "aie.objectfifo.acquire"() <{objFifo_name = @of1, port = 1 : i32, size = 1 : i32}> : () -> !aie.objectfifosubview<memref<16xi32>>

%5 = aie.objectfifo.subview.access %4[0] : !aie.objectfifosubview<memref<16xi32>> -> memref<16xi32>

// CHECK-NEXT: %{{.*}} = aie.objectfifo.subview.access %{{.*}}[0] : !aie.objectfifosubview<memref<16xi32>> -> memref<16xi32>
// CHECK-GENERIC-NEXT: %{{.*}} = "aie.objectfifo.subview.access"(%{{.*}}) <{index = 0 : i32}> : (!aie.objectfifosubview<memref<16xi32>>) -> memref<16xi32>

aie.objectfifo.release @of1(Consume, 1)

// CHECK-NEXT: aie.objectfifo.release @of1(Consume, 1)
// CHECK-GENERIC-NEXT: "aie.objectfifo.release"() <{objFifo_name = @of1, port = 1 : i32, size = 1 : i32}> : () -> ()

aie.end

// CHECK-NEXT: aie.end
// CHECK-GENERIC-NEXT: "aie.end"() : () -> ()

} // core
} // device
