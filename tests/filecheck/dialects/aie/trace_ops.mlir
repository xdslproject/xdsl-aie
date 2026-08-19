// RUN: XDSL_GENERIC_ROUNDTRIP
// RUN: AIE_GENERIC_ROUNDTRIP

// aie.trace must sit inside an aie.device; the host/start config ops sit in the
// runtime sequence.

aie.device(npu2) {
  %0 = aie.tile(0, 2)
  "aie.trace"(%0) <{sym_name = "trace_core_1"}> ({
    "aie.trace.mode"() <{mode = 0 : i32}> : () -> ()
    "aie.trace.packet"() <{type = 0 : i32}> : () -> ()
    "aie.trace.event"() <{event = #aie.trace_event<"INSTR_EVENT_0">}> : () -> ()
    "aie.trace.event"() <{event = #aie.trace_event<"LOCK_STALL">}> : () -> ()
    "aie.trace.start"() <{broadcast = 15 : i32}> : () -> ()
    "aie.trace.stop"() <{broadcast = 14 : i32}> : () -> ()
    "aie.end"() : () -> ()
  }) : (index) -> ()
  aie.runtime_sequence() {
    "aie.trace.host_config"() <{buffer_size = 65536 : i32, egress_shim_col = 0 : i32, reuse_output_buffer = false, routing = 0 : i32}> : () -> ()
    "aie.trace.start_config"() <{trace_config = @trace_core_1}> : () -> ()
  }
}

// CHECK-GENERIC:      "builtin.module"() ({
// CHECK-GENERIC-NEXT:   "aie.device"() <{device = 9 : i32, sym_name = "main"}> ({
// CHECK-GENERIC-NEXT:     %0 = "aie.tile"() <{col = 0 : i32, row = 2 : i32}> : () -> index
// CHECK-GENERIC-NEXT:     "aie.trace"(%0) <{sym_name = "trace_core_1"}> ({
// CHECK-GENERIC-NEXT:       "aie.trace.mode"() <{mode = 0 : i32}> : () -> ()
// CHECK-GENERIC-NEXT:       "aie.trace.packet"() <{type = 0 : i32}> : () -> ()
// CHECK-GENERIC-NEXT:       "aie.trace.event"() <{event = #aie.trace_event<"INSTR_EVENT_0">}> : () -> ()
// CHECK-GENERIC-NEXT:       "aie.trace.event"() <{event = #aie.trace_event<"LOCK_STALL">}> : () -> ()
// CHECK-GENERIC-NEXT:       "aie.trace.start"() <{broadcast = 15 : i32}> : () -> ()
// CHECK-GENERIC-NEXT:       "aie.trace.stop"() <{broadcast = 14 : i32}> : () -> ()
// CHECK-GENERIC-NEXT:       "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:     }) : (index) -> ()
// CHECK-GENERIC-NEXT:     "aie.runtime_sequence"() <{sym_name = "sequence"}> ({
// CHECK-GENERIC-NEXT:       "aie.trace.host_config"() <{buffer_size = 65536 : i32, egress_shim_col = 0 : i32, reuse_output_buffer = false, routing = 0 : i32}> : () -> ()
// CHECK-GENERIC-NEXT:       "aie.trace.start_config"() <{trace_config = @trace_core_1}> : () -> ()
// CHECK-GENERIC-NEXT:     }) : () -> ()
// CHECK-GENERIC-NEXT:     "aie.end"() : () -> ()
// CHECK-GENERIC-NEXT:   }) : () -> ()
// CHECK-GENERIC-NEXT: }) : () -> ()
