// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP

"builtin.module"() ({
  "aie.device"() <{device = 4 : i32}> ({
    %0 = "aie.tile"() <{col = 0 : i32, row = 0 : i32}> : () -> index
    %1 = "aie.tile"() <{col = 2 : i32, row = 0 : i32}> : () -> index
    "aiex.runtime_sequence"() ({
    ^bb0(%arg0 : memref<8xi16>, %arg1 : memref<10xi32>):
      %2 = "aiex.dma_configure_task"(%0) <{channel = 0 : i32, direction = 1 : i32, issue_token = true}> ({
        "aie.dma_bd"(%arg0) <{bd_id = 7 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
        "aie.end"() : () -> ()
      }) : (index) -> index
      %3 = "aiex.dma_configure_task"(%1) <{channel = 1 : i32, direction = 0 : i32, issue_token = true, repeat_count = 2 : i32}> ({
        "aie.dma_bd"(%arg1) <{bd_id = 8 : i32, len = 10 : i32, offset = 0 : i32}> : (memref<10xi32>) -> ()
        "aie.end"() : () -> ()
      }) : (index) -> index
      "aiex.dma_start_task"(%2) : (index) -> ()
      "aiex.dma_start_task"(%3) : (index) -> ()
      "aiex.dma_await_task"(%2) : (index) -> ()
      "aiex.dma_await_task"(%3) : (index) -> ()
    }) : () -> ()
    "aie.end"() : () -> ()
  }) : () -> ()
}) : () -> ()


// CHECK-GENERIC:      "builtin.module"() ({
// CHECK-GENERIC-NEXT:   "aie.device"() <{device = 4 : i32}> ({
// CHECK-GENERIC-NEXT:     %0 = "aie.tile"() <{col = 0 : i32, row = 0 : i32}> : () -> index
// CHECK-GENERIC-NEXT:     %1 = "aie.tile"() <{col = 2 : i32, row = 0 : i32}> : () -> index
// CHECK-GENERIC-NEXT:     "aiex.runtime_sequence"() ({
// CHECK-GENERIC-NEXT:     ^0(%arg0 : memref<8xi16>, %arg1 : memref<10xi32>):
// CHECK-GENERIC-NEXT:       %2 = "aiex.dma_configure_task"(%0) <{channel = 0 : i32, direction = 1 : i32, issue_token = true}> ({
// CHECK-GENERIC-NEXT:         "aie.dma_bd"(%arg0) <{bd_id = 7 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
// CHECK-GENERIC-NEXT:         "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:       }) : (index) -> index
// CHECK-GENERIC-NEXT:       %3 = "aiex.dma_configure_task"(%1) <{channel = 1 : i32, direction = 0 : i32, issue_token = true, repeat_count = 2 : i32}> ({
// CHECK-GENERIC-NEXT:         "aie.dma_bd"(%arg1) <{bd_id = 8 : i32, len = 10 : i32, offset = 0 : i32}> : (memref<10xi32>) -> ()
// CHECK-GENERIC-NEXT:         "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:       }) : (index) -> index
// CHECK-GENERIC-NEXT:       "aiex.dma_start_task"(%2) : (index) -> ()
// CHECK-GENERIC-NEXT:       "aiex.dma_start_task"(%3) : (index) -> ()
// CHECK-GENERIC-NEXT:       "aiex.dma_await_task"(%2) : (index) -> ()
// CHECK-GENERIC-NEXT:       "aiex.dma_await_task"(%3) : (index) -> ()
// CHECK-GENERIC-NEXT:     }) : () -> ()
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT: }) : () -> ()

// -----

"builtin.module"() ({
  "aie.device"() <{device = 4 : i32}> ({
    %0 = "aie.tile"() <{col = 0 : i32, row = 0 : i32}> : () -> index
    %1 = "aie.tile"() <{col = 0 : i32, row = 2 : i32}> : () -> index
    "aiex.runtime_sequence"() ({
    ^bb0(%arg0: memref<8xi16>, %arg1: memref<10xi32>):
      %2 = "aiex.dma_configure_task"(%0) <{channel = 0 : i32, direction = 1 : i32}> ({
        "aie.dma_bd"(%arg0) <{bd_id = 0 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
        "aie.next_bd"()[^bb1] : () -> ()
      ^bb1:  // pred: ^bb0
        "aie.dma_bd"(%arg1) <{bd_id = 1 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<10xi32>) -> ()
        "aie.next_bd"()[^bb2] : () -> ()
      ^bb2:  // pred: ^bb1
        "aie.dma_bd"(%arg0) <{bd_id = 2 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<8xi16>) -> ()
        "aie.end"() : () -> ()
      }) : (index) -> index
    }) : () -> ()
    "aie.end"() : () -> ()
  }) : () -> ()
}) : () -> ()


// CHECK-GENERIC:      "builtin.module"() ({
// CHECK-GENERIC-NEXT:   "aie.device"() <{device = 4 : i32}> ({
// CHECK-GENERIC-NEXT:     %0 = "aie.tile"() <{col = 0 : i32, row = 0 : i32}> : () -> index
// CHECK-GENERIC-NEXT:     %1 = "aie.tile"() <{col = 0 : i32, row = 2 : i32}> : () -> index
// CHECK-GENERIC-NEXT:     "aiex.runtime_sequence"() ({
// CHECK-GENERIC-NEXT:     ^0(%arg0 : memref<8xi16>, %arg1 : memref<10xi32>):
// CHECK-GENERIC-NEXT:       %2 = "aiex.dma_configure_task"(%0) <{channel = 0 : i32, direction = 1 : i32}> ({
// CHECK-GENERIC-NEXT:         "aie.dma_bd"(%arg0) <{bd_id = 0 : i32, len = 8 : i32, offset = 0 : i32}> : (memref<8xi16>) -> ()
// CHECK-GENERIC-NEXT:         "aie.next_bd"() [^1] : () -> ()
// CHECK-GENERIC-NEXT:       ^1:
// CHECK-GENERIC-NEXT:         "aie.dma_bd"(%arg1) <{bd_id = 1 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<10xi32>) -> ()
// CHECK-GENERIC-NEXT:         "aie.next_bd"() [^2] : () -> ()
// CHECK-GENERIC-NEXT:       ^2:
// CHECK-GENERIC-NEXT:         "aie.dma_bd"(%arg0) <{bd_id = 2 : i32, len = 10 : i32, offset = 2 : i32}> : (memref<8xi16>) -> ()
// CHECK-GENERIC-NEXT:         "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:       }) : (index) -> index
// CHECK-GENERIC-NEXT:     }) : () -> ()
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT: }) : () -> ()
