"""
Port of the AMD Xilinx AIE dialect for programming the AIEs on the AMD Xilinx Versal FPGA architecture.
AIE is a hardened systolic array present in the Versal devices. The dialect describes netlists of AIE
components and it can be lowered to the processor's assembly using the vendor's compiler. A description
of the original dialect can be found here https://xilinx.github.io/mlir-aie/AIEDialect.html
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Generic, cast

from typing_extensions import Self
from xdsl.dialects import builtin
from xdsl.dialects.builtin import (
    I32,
    AnyIntegerAttr,
    ArrayAttr,
    BoolAttr,
    Float32Type,
    IndexType,
    IntAttr,
    IntegerAttr,
    IntegerType,
    MemrefLayoutAttr,
    MemRefType,
    ModuleOp,
    NoneAttr,
    Signedness,
    StringAttr,
    SymbolRefAttr,
    i32,
)
from xdsl.dialects.func import FuncOp
from xdsl.ir import (
    Attribute,
    AttributeInvT,
    Block,
    Data,
    Dialect,
    EnumAttribute,
    OpaqueSyntaxAttribute,
    Operation,
    OpResult,
    ParametrizedAttribute,
    Region,
    SSAValue,
    StrEnum,
    TypeAttribute,
)
from xdsl.irdl import (
    IRDLOperation,
    ParameterDef,
    attr_def,
    irdl_attr_definition,
    irdl_op_definition,
    operand_def,
    opt_attr_def,
    opt_prop_def,
    prop_def,
    region_def,
    result_def,
    successor_def,
    traits_def,
    var_operand_def,
)
from xdsl.parser import AttrParser, Parser
from xdsl.printer import Printer
from xdsl.traits import (
    HasParent,
    IsTerminator,
    SingleBlockImplicitTerminator,
    SymbolOpInterface,
    SymbolTable,
    ensure_terminator,
)
from xdsl.utils.exceptions import VerifyException
from xdsl.utils.hints import isa

CASCADE_SIZE = 384


class IntStrEnum(StrEnum):
    @classmethod
    def get_sequence(cls) -> Sequence[Self]:
        return tuple(x for x in cls)

    @classmethod
    def from_int(cls, value: int) -> Self:
        return cls.get_sequence()[value - 1]

    def get_int(self) -> int:
        return self.get_sequence().index(self) + 1


class AIEDeviceEnum(IntStrEnum):
    xcvc1902 = "xcvc1902"
    xcve2302 = "xcve2302"
    xcve2802 = "xcve2802"
    npu1 = "npu1"
    npu1_1col = "npu1_1col"
    npu1_2col = "npu1_2col"
    npu1_3col = "npu1_3col"
    npu1_4col = "npu1_4col"
    npu2 = "npu2"


class ObjectFifoPortEnum(IntStrEnum):
    Consume = "Consume"
    Produce = "Produce"


class DMAChannelDirEnum(StrEnum):
    S2MM = "S2MM"
    MM2S = "MM2S"


@irdl_attr_definition
class DMAChannelDirAttr(EnumAttribute[DMAChannelDirEnum]):
    name = "aie.channel_dir"


class WireBundleEnum(StrEnum):
    Core = "Core"
    DMA = "DMA"
    FIFO = "FIFO"
    South = "South"
    West = "West"
    North = "North"
    East = "East"
    PLIO = "PLIO"
    NOC = "NOC"
    Trace = "Trace"


@irdl_attr_definition
class WireBundleAttr(EnumAttribute[WireBundleEnum]):
    name = "aie.wire_bundle"


class LockActionEnum(StrEnum):
    Acquire = "Acquire"
    AcquireGreaterEqual = "AcquireGreaterEqual"
    Release = "Release"


@irdl_attr_definition
class LockActionAttr(EnumAttribute[LockActionEnum]):
    name = "aie.lock_action"


class LockBlockingEnum(StrEnum):
    NonBlocking = "NonBlocking"
    Blocking = "Blocking"


@irdl_attr_definition
class LockBlockingAttr(EnumAttribute[LockActionEnum]):
    name = "aie.lock_blocking"


class BufferTypeEnum(StrEnum):
    A = "A"
    B = "B"


@irdl_attr_definition
class BufferTypeAttr(EnumAttribute[BufferTypeEnum]):
    name = "aie.buffer_type"


@irdl_attr_definition
class ObjectFIFO(Generic[AttributeInvT], ParametrizedAttribute, TypeAttribute):
    name = "aie.objectfifo"

    buffer: ParameterDef[AttributeInvT]

    @staticmethod
    def from_element_type_and_shape(
        referenced_type: AttributeInvT,
        shape: Iterable[int | IntAttr],
        layout: MemrefLayoutAttr | NoneAttr = NoneAttr(),
        memory_space: Attribute = NoneAttr(),
    ) -> ObjectFIFO[AttributeInvT]:
        return ObjectFIFO(
            [builtin.MemRefType(referenced_type, shape, layout, memory_space)]
        )


@irdl_attr_definition
class ObjectFIFOSubview(Generic[AttributeInvT], ParametrizedAttribute, TypeAttribute):
    name = "aie.objectfifosubview"

    buffer: ParameterDef[builtin.MemRefType[AttributeInvT]]

    @staticmethod
    def from_element_type_and_shape(
        element_type: AttributeInvT,
        shape: Iterable[int | IntAttr],
    ) -> ObjectFIFOSubview[AttributeInvT]:
        return ObjectFIFOSubview([builtin.MemRefType(element_type, shape)])


class BDDimLayout(tuple[int]): ...


class BDDimLayoutArray(tuple[BDDimLayout, ...]): ...


class BDDimLayoutArrayArray(tuple[BDDimLayoutArray, ...]): ...


@irdl_attr_definition
class BDDimLayoutArrayAttr(Data[BDDimLayoutArray], OpaqueSyntaxAttribute):
    name = "aie.bd_dim_layout_array"

    @classmethod
    def parse_parameter(cls, parser: AttrParser) -> BDDimLayoutArray:
        parser.parse_punctuation("[")
        parser.parse_punctuation("]")
        return BDDimLayoutArray(tuple())

    def print_parameter(self, printer: Printer) -> None:
        printer.print_string(f"{list(self.data)}")


@irdl_attr_definition
class BDDimLayoutArrayArrayAttr(Data[BDDimLayoutArrayArray], OpaqueSyntaxAttribute):
    name = "aie.bd_dim_layout_array_array"

    @classmethod
    def parse_parameter(cls, parser: AttrParser) -> BDDimLayoutArrayArray:
        parser.parse_punctuation("[")
        parser.parse_punctuation("[")
        parser.parse_punctuation("]")
        parser.parse_punctuation("]")
        return BDDimLayoutArrayArray(tuple(tuple()))

    def print_parameter(self, printer: Printer) -> None:
        printer.print_string("[[]]")


@irdl_op_definition
class SwitchboxOp(IRDLOperation):
    name = "aie.switchbox"

    tile = operand_def(IndexType())
    region = region_def()
    result = result_def(IndexType())

    def __init__(self, tile: Operation | SSAValue, region: Region):
        super().__init__(operands=[tile], regions=[region], result_types=[IndexType()])

    def print(self, printer: Printer):
        printer.print("(")
        printer.print_operand(self.tile)
        printer.print(") ")
        printer.print_region(self.region)

    @classmethod
    def parse(cls, parser: Parser) -> SwitchboxOp:
        parser.parse_characters("(")
        tile = parser.parse_operand()
        parser.parse_characters(")")
        region = parser.parse_region()

        return SwitchboxOp(tile, region)


@irdl_op_definition
class AMSelOp(IRDLOperation):
    name = "aie.amsel"
    arbiterID = attr_def(AnyIntegerAttr)
    msel = attr_def(AnyIntegerAttr)
    result = result_def(IndexType())

    traits = traits_def(HasParent(SwitchboxOp))

    def __init__(
        self, arbiterID: IntegerAttr[IntegerType], msel: IntegerAttr[IntegerType]
    ):
        super().__init__(
            attributes={"arbiterID": arbiterID, "msel": msel},
            result_types=[IndexType()],
        )

    def verify_(self) -> None:
        if self.arbiterID.type != IntegerType(8):
            raise VerifyException("arbiterID has to be an 8-bit signless integer")
        if self.arbiterID.value.data < 0 or self.arbiterID.value.data > 5:
            raise VerifyException("arbiterID has to be in the range [0-5].")
        if self.msel.type != IntegerType(8):
            raise VerifyException("msel has to be an 8-bit signless integer")
        if self.msel.value.data < 0 or self.arbiterID.value.data > 3:
            raise VerifyException("msel has to be in the range [0-3].")


@irdl_op_definition
class BufferOp(IRDLOperation):
    name = "aie.buffer"
    tile = operand_def(IndexType())
    buffer = result_def(builtin.MemRefType)
    sym_name = attr_def(StringAttr)

    def __init__(
        self,
        tile: Operation | SSAValue,
        element_type: Attribute,
        shape: ArrayAttr[IntAttr],
        sym_name: StringAttr,
    ):
        buffer_type = builtin.MemRefType(element_type, shape)
        super().__init__(
            operands=[tile],
            attributes={"sym_name": sym_name},
            result_types=[buffer_type],
        )

    assembly_format = "`(` $tile `)` attr-dict `:` type($buffer)"


@irdl_op_definition
class TileOp(IRDLOperation):
    name = "aie.tile"
    col = prop_def(IntegerAttr[IntegerType])
    row = prop_def(IntegerAttr[IntegerType])
    result = result_def(IndexType())

    def __init__(
        self, col: int | IntegerAttr[IntegerType], row: int | IntegerAttr[IntegerType]
    ):
        if isinstance(col, int):
            col = IntegerAttr.from_int_and_width(col, 32)
        if isinstance(row, int):
            row = IntegerAttr.from_int_and_width(row, 32)
        super().__init__(
            properties={"col": col, "row": row}, result_types=[IndexType()]
        )

    def print(self, printer: Printer):
        printer.print("(")
        printer.print(self.col.value.data)
        printer.print(", ")
        printer.print(self.row.value.data)
        printer.print(")")

    @classmethod
    def parse(cls, parser: Parser) -> TileOp:
        parser.parse_characters("(")
        col = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(",")
        row = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(")")

        return TileOp(col, row)


@irdl_op_definition
class ShimMuxOp(IRDLOperation):
    name = "aie.shimmux"

    tile = operand_def(IndexType())

    def __init__(self, tile: Operation | SSAValue):
        super().__init__(operands=[tile], result_types=[IndexType()])


@irdl_op_definition
class ConnectOp(IRDLOperation):
    name = "aie.connect"
    sourceBundle = attr_def(WireBundleAttr)
    sourceChannel = attr_def(AnyIntegerAttr)
    destBundle = attr_def(WireBundleAttr)
    destChannel = attr_def(AnyIntegerAttr)

    traits = traits_def(HasParent(SwitchboxOp, ShimMuxOp))

    def __init__(
        self,
        sourceBundle: WireBundleAttr,
        sourceChannel: int | AnyIntegerAttr,
        destBundle: WireBundleAttr,
        destChannel: int | AnyIntegerAttr,
    ):
        if isinstance(sourceChannel, int):
            sourceChannel = IntegerAttr(sourceChannel, IntegerType(8))
        if isinstance(destChannel, int):
            destChannel = IntegerAttr(destChannel, IntegerType(8))
        super().__init__(
            attributes={
                "sourceBundle": sourceBundle,
                "sourceChannel": sourceChannel,
                "destBundle": destBundle,
                "destChannel": destChannel,
            }
        )

    def print(self, printer: Printer):
        printer.print(
            "<",
            self.sourceBundle.data,
            ": ",
            self.sourceChannel.value.data,
            ", ",
            self.destBundle.data,
            ": ",
            self.destChannel.value.data,
            ">",
        )

    @classmethod
    def parse(cls, parser: Parser) -> ConnectOp:
        parser.parse_characters("<")
        sourceBundle = WireBundleAttr(WireBundleAttr.parse_parameter(parser))
        parser.parse_characters(":")
        sourceChannel = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(",")
        destBundle = WireBundleAttr(WireBundleAttr.parse_parameter(parser))
        parser.parse_characters(":")
        sourceChannel = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(">")

        return ConnectOp(sourceBundle, sourceChannel, destBundle, sourceChannel)

    def verify_(self) -> None:
        if self.sourceChannel.type != i32:
            raise VerifyException("sourceChannel has to be a 32-bit signless integer")
        if self.sourceChannel.value.data < 0:
            raise VerifyException("sourceChannel has to be equal or greater than 0")
        if self.destChannel.type != i32:
            raise VerifyException("destChannel has to be a 32-bit signless integer")
        if self.destChannel.value.data < 0:
            raise VerifyException("destChannel has to be equal or greater than 0")


@irdl_op_definition
class CoreOp(IRDLOperation):
    name = "aie.core"

    tile = operand_def(IndexType)

    result = result_def(IndexType)

    stack_size = opt_prop_def(IntegerAttr[IntegerType])

    link_with = opt_prop_def(StringAttr)
    elf_file = opt_prop_def(StringAttr)

    dynamic_objfifo_lowering = opt_prop_def(BoolAttr)

    region = region_def()

    def __init__(
        self,
        stackSize: IntegerAttr[IntegerType] | None,
        tile: Operation | SSAValue,
        region: Region,
        link_with: StringAttr | None = None,
    ):
        if stackSize is None:
            stackSize = IntegerAttr.from_int_and_width(1024, 32)
        super().__init__(
            properties={"stack_size": stackSize, "link_with": link_with},
            operands=[tile],
            regions=[region],
            result_types=[IndexType()],
        )

    def print(self, printer: Printer):
        printer.print("(")
        printer.print_operand(self.tile)
        printer.print(") ")
        printer.print_region(self.region)
        if self.link_with is not None:
            printer.print(" { link_with=", self.link_with, " }")

    @classmethod
    def parse(cls, parser: Parser) -> CoreOp:
        parser.parse_characters("(")
        tile = parser.parse_operand()
        parser.parse_characters(")")
        region = parser.parse_region()
        attr_dict = parser.parse_optional_attr_dict()

        link_with = None
        if attr_dict:
            assert isinstance(attr_dict["link_with"], StringAttr)
            link_with = attr_dict["link_with"]

        stackSize = None
        return CoreOp(stackSize, tile, region, link_with)


@irdl_op_definition
class DMABDOp(IRDLOperation):
    name = "aie.dma_bd"
    offset = attr_def(IntegerAttr[IntegerType])
    length = attr_def(IntegerAttr[IntegerType])
    buffer = operand_def(builtin.MemRefType)
    dimensions = opt_attr_def(
        IntegerAttr[IntegerType]
    )  # TODO: this should be implemented as a DimTupleArrayAttr: check https://xilinx.github.io/mlir-aie/AIEDialect.html

    def __init__(
        self,
        offset: IntegerAttr[IntegerType],
        length: IntegerAttr[IntegerType],
        dimensions: None | IntegerAttr[IntegerType],
        buffer: Operation | SSAValue,
    ):
        if dimensions is None:
            super().__init__(
                attributes={"offset": offset, "length": length},
                operands=[buffer],
            )
        else:
            super().__init__(
                attributes={
                    "offset": offset,
                    "length": length,
                    "dimensions": dimensions,
                },
                operands=[buffer],
            )

    def print(self, printer: Printer):
        printer.print("(")
        printer.print_operand(self.buffer)
        printer.print(
            ": ",
            self.buffer.type,
            ", ",
            self.offset.value.data,
            ", ",
            self.length.value.data,
            ")",
        )

    @classmethod
    def parse(cls, parser: Parser) -> DMABDOp:
        parser.parse_characters("(")
        buffer = parser.parse_operand()
        parser.parse_characters(":")
        parser.parse_type()
        parser.parse_characters(",")
        offset = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(",")
        length = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(")")

        return DMABDOp(offset, length, None, buffer)


@irdl_op_definition
class DMABDPACKETOp(IRDLOperation):
    name = "aie.dma_bd_packet"
    packet_type = attr_def(IntegerAttr[IntegerType])
    packet_id = attr_def(IntegerAttr[IntegerType])

    def __init__(
        self, packet_type: IntegerAttr[IntegerType], packet_id: IntegerAttr[IntegerType]
    ):
        super().__init__(
            attributes={"packet_type": packet_type, "packet_id": packet_id}
        )

    def print(self, printer: Printer):
        printer.print("(")
        printer.print(self.packet_type.value.data)
        printer.print(",")
        printer.print(self.packet_id.value.data)
        printer.print(")")

    @classmethod
    def parse(cls, parser: Parser) -> DMABDPACKETOp:
        parser.parse_characters("(")
        packet_type = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(",")
        packet_id = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(")")

        return DMABDPACKETOp(packet_type, packet_id)


@irdl_op_definition
class MemOp(IRDLOperation):
    name = "aie.mem"

    tile = operand_def(IndexType())
    region = region_def()
    result = result_def(IndexType())

    def __init__(self, tile: Operation | SSAValue, region: Region):
        super().__init__(operands=[tile], result_types=[IndexType()], regions=[region])

    def print(self, printer: Printer):
        printer.print("(")
        printer.print(self.tile)
        printer.print(")")
        printer.print_region(self.region)

    @classmethod
    def parse(cls, parser: Parser) -> MemOp:
        parser.parse_characters("(")
        tile = parser.parse_operand()
        parser.parse_characters(")")
        region = parser.parse_region()

        return MemOp(tile, region)


@irdl_op_definition
class MemTileDMAOp(IRDLOperation):
    name = "aie.memTileDMA"

    tile = operand_def(IndexType())

    def __init__(self, tile: Operation | SSAValue):
        super().__init__(operands=[tile], result_types=[IndexType()])


@irdl_op_definition
class ShimDMAOp(IRDLOperation):
    name = "aie.shimDMA"

    tile = operand_def(IndexType())

    def __init__(self, tile: Operation | SSAValue):
        super().__init__(operands=[tile], result_types=[IndexType()])


@irdl_op_definition
class DMAStartOp(IRDLOperation):
    name = "aie.dma_start"
    channelDir = attr_def(DMAChannelDirAttr)
    channelIndex = attr_def(IntegerAttr[IntegerType])
    dest = successor_def()
    chain = successor_def()

    traits = traits_def(
        IsTerminator(), HasParent(MemOp, MemTileDMAOp, FuncOp, ShimDMAOp)
    )

    def __init__(
        self,
        channelDir: Attribute,
        channelIndex: IntegerAttr[IntegerType],
        dest: Block,
        chain: Block,
    ):
        super().__init__(
            attributes={"channelDir": channelDir, "channelIndex": channelIndex},
            successors=[dest, chain],
        )

    def print(self, printer: Printer):
        printer.print(
            "(", self.channelDir.data, ", ", self.channelIndex.value.data, ", "
        )
        printer.print_block_name(self.dest)
        printer.print(", ")
        printer.print_block_name(self.chain)
        printer.print(")")

    @classmethod
    def parse(cls, parser: Parser) -> DMAStartOp:
        parser.parse_characters("(")
        channelDir = DMAChannelDirAttr(DMAChannelDirAttr.parse_parameter(parser))
        parser.parse_characters(",")
        channelIndex = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(",")
        dest = parser.parse_successor()
        parser.parse_characters(",")
        chain = parser.parse_successor()
        parser.parse_characters(")")

        return DMAStartOp(channelDir, channelIndex, dest, chain)


@irdl_op_definition
class DebugOp(IRDLOperation):
    name = "aie.debug"
    arg = operand_def()

    def __init__(self, arg: Operation | SSAValue):
        super().__init__(operands=[arg])


@irdl_op_definition
class EndOp(IRDLOperation):
    name = "aie.end"

    def __init__(self):
        super().__init__()

    traits = traits_def(IsTerminator())

    assembly_format = "attr-dict"


@irdl_op_definition
class DeviceOp(IRDLOperation):
    name = "aie.device"

    region = region_def("single_block")

    device = prop_def(IntegerAttr[IntegerType])
    traits = traits_def(
        SymbolTable(), SingleBlockImplicitTerminator(EndOp), HasParent(ModuleOp)
    )

    def __init__(self, device: IntegerAttr[IntegerType], region: Region):
        super().__init__(properties={"device": device}, regions=[region])

    def print(self, printer: Printer):
        printer.print("(")
        printer.print(AIEDeviceEnum.from_int(self.device.value.data).value)
        printer.print(") ")
        printer.print_region(self.region, print_block_terminators=False)

    @classmethod
    def parse(cls, parser: Parser) -> DeviceOp:
        parser.parse_characters("(")
        device = parser.parse_str_enum(AIEDeviceEnum)
        parser.parse_characters(")")
        region = parser.parse_region()

        device_op = cls(IntegerAttr(device.get_int(), 32), region)

        for trait in device_op.get_traits_of_type(SingleBlockImplicitTerminator):
            ensure_terminator(device_op, trait)

        return device_op


@irdl_op_definition
class ExternalBufferOp(IRDLOperation):
    name = "aie.external_buffer"

    sym_name = attr_def(StringAttr)
    buffer = result_def(builtin.MemRefType)

    def __init__(
        self,
        sym_name: str,
        shape: ArrayAttr[IntAttr],
        element_type: Attribute,
    ):
        builtin.MemRefType(element_type, shape)
        super().__init__(
            attributes={"sym_name": StringAttr(sym_name)},
            result_types=[builtin.MemRefType(element_type, shape)],
        )

    assembly_format = "attr-dict `:` type($buffer)"


@irdl_op_definition
class FlowOp(IRDLOperation):
    name = "aie.flow"

    sourceBundle = attr_def(WireBundleAttr)
    sourceChannel = attr_def(IntegerAttr[IntegerType])
    destBundle = attr_def(WireBundleAttr)
    destChannel = attr_def(IntegerAttr[IntegerType])
    source = operand_def(IndexType())
    dest = operand_def(IndexType())

    def __init__(
        self,
        sourceBundle: WireBundleAttr,
        sourceChannel: IntegerAttr[IntegerType],
        destBundle: WireBundleAttr,
        destChannel: IntegerAttr[IntegerType],
        source: Operation | SSAValue,
        dest: Operation | SSAValue,
    ):
        super().__init__(
            attributes={
                "sourceBundle": sourceBundle,
                "sourceChannel": sourceChannel,
                "destBundle": destBundle,
                "destChannel": destChannel,
            },
            operands=[source, dest],
        )

    def print(self, printer: Printer):
        printer.print("(")
        printer.print(self.source)
        printer.print(",")
        printer.print(self.sourceBundle.data)
        printer.print(":")
        printer.print(self.sourceChannel.value.data)
        printer.print(",")
        printer.print(self.dest)
        printer.print(",")
        printer.print(self.destBundle.data)
        printer.print(":")
        printer.print(self.destChannel.value.data)
        printer.print(")")

    @classmethod
    def parse(cls, parser: Parser) -> FlowOp:
        parser.parse_characters("(")
        source = parser.parse_operand()
        parser.parse_characters(",")
        sourceBundle = WireBundleAttr(WireBundleAttr.parse_parameter(parser))
        parser.parse_characters(":")
        sourceChannel = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(",")
        dest = parser.parse_operand()
        parser.parse_characters(",")
        destBundle = WireBundleAttr(WireBundleAttr.parse_parameter(parser))
        parser.parse_characters(":")
        destChannel = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(")")

        return FlowOp(
            sourceBundle, sourceChannel, destBundle, destChannel, source, dest
        )


@irdl_op_definition
class GetCascadeOp(IRDLOperation):
    name = "getCascade"

    traits = traits_def(HasParent(CoreOp))

    def __init__(self):
        super().__init__(result_types=[IntegerType(CASCADE_SIZE)])


@irdl_op_definition
class GetStreamOp(IRDLOperation):
    name = "aie.getStream"

    channel = operand_def(i32)
    result = result_def(IntegerType)

    traits = traits_def(HasParent(CoreOp))

    def __init__(self, channel: Operation | SSAValue):
        super().__init__(
            operands=[channel],
            result_types=[i32],  # TODO: the result can be of several types.
        )


@irdl_op_definition
class LockOp(IRDLOperation):
    name = "aie.lock"

    tile = operand_def(IndexType())
    lockID = opt_attr_def(IntegerAttr[IntegerType])
    init = opt_attr_def(IntegerAttr[IntegerType])
    result = result_def(IndexType())
    sym_name = opt_attr_def(StringAttr)

    def __init__(
        self,
        lockID: IntegerAttr[IntegerType],
        init: IntegerAttr[IntegerType] | None,
        tile: Operation | SSAValue,
        sym_name: StringAttr | None,
    ):
        super().__init__(
            attributes={"lockID": lockID, "init": init, "sym_name": sym_name},
            operands=[tile],
            result_types=[IndexType()],
        )

    def print(self, printer: Printer):
        printer.print("(")
        printer.print(self.tile)
        if self.lockID:
            printer.print(",")
            printer.print(self.lockID.value.data)
            printer.print(")")
        if self.sym_name:
            printer.print("{")
            printer.print("sym_name = ")
            printer.print(self.sym_name)
            printer.print("}")

    @classmethod
    def parse(cls, parser: Parser) -> LockOp:
        parser.parse_characters("(")
        tile = parser.parse_operand()
        parser.parse_characters(",")
        lockID = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        init = parser.parse_optional_integer()
        parser.parse_characters(")")
        sym_name = None
        attr_dict = parser.parse_optional_attr_dict()
        if attr_dict:
            assert isinstance(attr_dict["sym_name"], StringAttr)
            sym_name = attr_dict["sym_name"]

        if init:
            init = IntegerAttr.from_int_and_width(init, 32)

        return LockOp(
            lockID, None, tile, sym_name
        )  # TODO: argument should be init but Pyright fails


@irdl_op_definition
class MasterSetOp(IRDLOperation):
    name = "aie.masterset"

    destBundle = attr_def(WireBundleAttr)
    destChannel = attr_def(IntegerAttr[IntegerType])
    amsels = operand_def(IndexType())

    traits = traits_def(HasParent(SwitchboxOp))

    def __init__(
        self,
        destBundle: WireBundleAttr,
        destChannel: IntegerAttr[IntegerType],
        amsels: Operation | SSAValue,
    ):
        super().__init__(
            attributes={"destBundle": destBundle, "destChannel": destChannel},
            operands=[amsels],
            result_types=[IndexType()],
        )


@irdl_op_definition
class NextBDOp(IRDLOperation):
    name = "aie.next_bd"

    dest = successor_def()

    traits = traits_def(
        HasParent(MemOp, MemTileDMAOp, FuncOp, ShimDMAOp), IsTerminator()
    )

    def __init__(self, dest: Block):
        super().__init__(successors=[dest])

    def print(self, printer: Printer):
        printer.print(" ")
        printer.print_block_name(self.dest)

    @classmethod
    def parse(cls, parser: Parser) -> NextBDOp:
        dest = parser.parse_successor()

        return NextBDOp(dest)


@irdl_op_definition
class ObjectFifoAcquireOp(IRDLOperation):
    name = "aie.objectfifo.acquire"

    port = prop_def(IntegerAttr[IntegerType])
    size = prop_def(IntegerAttr[IntegerType])
    objFifo_name = prop_def(SymbolRefAttr)

    result = result_def(ObjectFIFOSubview)

    def __init__(
        self,
        port: IntegerAttr[IntegerType],
        size: IntegerAttr[IntegerType],
        object_fifo: str | SymbolRefAttr,
        shape: Iterable[int | IntAttr],
        element_type: Attribute,
    ):
        if isinstance(object_fifo, str):
            object_fifo = SymbolRefAttr(object_fifo)

        result_subview = ObjectFIFOSubview[Attribute].from_element_type_and_shape(
            element_type, shape
        )
        super().__init__(
            properties={"objFifo_name": object_fifo, "port": port, "size": size},
            result_types=[result_subview],
        )

    def print(self, printer: Printer):
        printer.print(f" @{self.objFifo_name.root_reference.data}")
        printer.print(
            f"({ObjectFifoPortEnum.from_int(self.port.value.data).value}, {self.size.value.data})"
        )
        printer.print(" : !aie.objectfifosubview<")
        assert isa(self.result.type, ObjectFIFOSubview[Attribute])
        printer.print(self.result.type.buffer)
        printer.print(">")

    @classmethod
    def parse(cls, parser: Parser) -> ObjectFifoAcquireOp:
        object_fifo = SymbolRefAttr(parser.parse_symbol_name())
        parser.parse_characters("(")
        port = parser.parse_str_enum(ObjectFifoPortEnum)
        parser.parse_characters(",")
        size = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(")")
        parser.parse_characters(":")
        parser.parse_characters("!aie.objectfifosubview")
        parser.parse_characters("<")
        ofifo_type = parser.parse_type()
        parser.parse_characters(">")
        assert isa(ofifo_type, MemRefType[Attribute])
        shape = ofifo_type.shape
        element_type = ofifo_type.element_type

        return ObjectFifoAcquireOp(
            IntegerAttr.from_int_and_width(port.get_int(), 32),
            size,
            object_fifo,
            shape,
            element_type,
        )


@irdl_op_definition
class ObjectFifoRegisterExternalBuffersOp(IRDLOperation):
    name = "aie.objectfifo.register_external_buffers"

    tile = operand_def(IndexType())
    externalBuffers = operand_def(builtin.MemRefType)
    object_fifo = attr_def(SymbolRefAttr)

    traits = traits_def(HasParent(DeviceOp))

    def __init__(
        self,
        tile: Operation | SSAValue,
        externalBuffers: Operation | SSAValue,
        object_fifo: str | SymbolRefAttr,
    ):
        if isinstance(object_fifo, str):
            object_fifo = SymbolRefAttr(object_fifo)

        super().__init__(
            operands=[tile, externalBuffers], attributes={"object_fifo": object_fifo}
        )

    def print(self, printer: Printer):
        assert isinstance(self.object_fifo, SymbolRefAttr)
        printer.print(
            f" {self.object_fifo} (",
            self.tile,
            ", {",
            self.externalBuffers,
            "}) : (",
            self.externalBuffers.type,
            ")",
        )

    @classmethod
    def parse(cls, parser: Parser) -> ObjectFifoRegisterExternalBuffersOp:
        object_fifo = SymbolRefAttr(parser.parse_symbol_name())
        parser.parse_characters("(")
        tile = parser.parse_operand()
        parser.parse_characters(",")
        parser.parse_characters("{")
        external_buffers = parser.parse_operand()
        parser.parse_characters("}")
        parser.parse_characters(")")
        parser.parse_characters(":")
        parser.parse_characters("(")
        parser.parse_type()
        parser.parse_characters(")")

        return ObjectFifoRegisterExternalBuffersOp(tile, external_buffers, object_fifo)


@irdl_op_definition
class ObjectFIFOSubviewAccessOp(IRDLOperation):
    name = "aie.objectfifo.subview.access"

    index = prop_def(IntegerAttr[IntegerType])
    subview = operand_def(ObjectFIFOSubview[Attribute])
    output = result_def(builtin.MemRefType)

    def __init__(self, index: IntegerAttr[IntegerType], subview: Operation | SSAValue):
        assert isinstance(subview, ObjectFifoAcquireOp)
        assert isa(subview.result.type, ObjectFIFOSubview[Attribute])
        subview.result.type.buffer
        result_type = builtin.MemRefType(
            subview.result.type.buffer.element_type, subview.result.type.buffer.shape
        )
        super().__init__(
            properties={"index": index}, operands=[subview], result_types=[result_type]
        )

    def print(self, printer: Printer):
        assert isa(self.subview.type, ObjectFIFOSubview[Attribute])
        printer.print(" ")
        printer.print_operand(self.subview)
        printer.print("[", self.index.value.data, "] : ")
        printer.print(
            "!aie.objectfifosubview<",
            self.subview.type.buffer,
            "> -> ",
            self.subview.type.buffer,
        )

    @classmethod
    def parse(cls, parser: Parser) -> ObjectFIFOSubviewAccessOp:
        subview = parser.parse_operand()
        if isinstance(subview, OpResult):
            subview = subview.op
        parser.parse_characters("[")
        index = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters("]")
        parser.parse_characters(":")
        parser.parse_characters("!aie.objectfifosubview")
        parser.parse_characters("<")
        parser.parse_type()  # subview type
        parser.parse_characters(">")
        parser.parse_characters("->")
        parser.parse_type()  # return type

        return ObjectFIFOSubviewAccessOp(index, subview)


@irdl_op_definition
class ObjectFifoOp(IRDLOperation):
    name = "aie.objectfifo"

    producerTile = operand_def(IndexType())
    consumerTiles = var_operand_def(IndexType())

    sym_name = prop_def(StringAttr)

    elemNumber = prop_def(IntegerAttr[IntegerType])
    elemType = prop_def(ObjectFIFO[Attribute])

    dimensionsToStream = prop_def(BDDimLayoutArrayAttr)
    dimensionsFromStreamPerConsumer = prop_def(BDDimLayoutArrayArrayAttr)

    via_DMA = prop_def(BoolAttr)
    plio = prop_def(BoolAttr)
    disable_synchronization = prop_def(BoolAttr)

    traits = traits_def(SymbolOpInterface(), HasParent(DeviceOp))

    def __init__(
        self,
        producerTile: Operation | SSAValue,
        consumerTiles: list[Operation | SSAValue],
        dimensionsToStream: BDDimLayoutArrayAttr,
        dimensionsFromStreamPerConsumer: BDDimLayoutArrayArrayAttr,
        disable_synchronization: bool | IntegerAttr[IntegerType],
        elemNumber: int | IntegerAttr[IntegerType],
        elemType: Attribute,
        plio: bool | BoolAttr,
        sym_name: str | StringAttr,
        via_DMA: bool | BoolAttr,
    ):
        if isinstance(disable_synchronization, bool):
            disable_synchronization = IntegerAttr.from_int_and_width(
                int(disable_synchronization), 1
            )
        if isinstance(elemNumber, int):
            elemNumber = IntegerAttr.from_int_and_width(elemNumber, 32)
        if isinstance(plio, bool):
            plio = IntegerAttr.from_int_and_width(int(plio), 1)
        if isinstance(sym_name, str):
            sym_name = StringAttr(sym_name)
        if isinstance(via_DMA, bool):
            via_DMA = IntegerAttr.from_int_and_width(int(via_DMA), 1)

        super().__init__(
            properties={
                "dimensionsFromStreamPerConsumer": dimensionsFromStreamPerConsumer,
                "dimensionsToStream": dimensionsToStream,
                "disable_synchronization": disable_synchronization,
                "elemNumber": elemNumber,
                "elemType": elemType,
                "plio": plio,
                "sym_name": sym_name,
                "via_DMA": via_DMA,
            },
            operands=[producerTile, *consumerTiles],
        )

    @staticmethod
    def from_referenced_type(
        producerTile: Operation | SSAValue,
        consumerTiles: list[Operation | SSAValue],
        name: str,
        elemNumber: IntegerAttr[IntegerType],
        referenced_type: Attribute,
        shape: Iterable[int | IntAttr],
    ) -> ObjectFifoOp:
        elemType = ObjectFIFO[Attribute].from_element_type_and_shape(
            referenced_type, shape
        )
        return ObjectFifoOp(
            producerTile,
            consumerTiles,
            BDDimLayoutArrayAttr(BDDimLayoutArray(tuple())),
            BDDimLayoutArrayArrayAttr(BDDimLayoutArrayArray(tuple(tuple()))),
            False,
            elemNumber,
            elemType,
            False,
            name,
            False,
        )

    def print(self, printer: Printer):
        printer.print(" @", self.sym_name.data, "(", self.producerTile, ", {")
        for i in range(len(self.consumerTiles) - 1):
            printer.print(self.consumerTiles[i], ", ")

        printer.print(self.consumerTiles[-1], "}, ")
        printer.print(self.elemNumber)

        printer.print(
            ") : !aie.objectfifo<",
            self.elemType.buffer,
            ">",
        )

    @classmethod
    def parse(cls, parser: Parser) -> ObjectFifoOp:
        name = parser.parse_symbol_name().data
        parser.parse_characters("(")
        producerTile = parser.parse_operand()
        parser.parse_characters(",")
        parser.parse_characters("{")
        consumerTiles: list[Operation | SSAValue] = []
        consumerTiles.append(parser.parse_operand())
        while not parser.parse_optional_characters("}"):
            parser.parse_characters(",")
            consumerTiles.append(parser.parse_operand())

        parser.parse_characters(",")
        elemNumber = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(":")
        parser.parse_type()
        parser.parse_characters(")")
        parser.parse_characters(":")
        parser.parse_characters("!aie.objectfifo")
        parser.parse_characters("<")
        objectfifo_type = parser.parse_type()
        parser.parse_characters(">")

        assert isa(objectfifo_type, MemRefType[Attribute])
        shape = objectfifo_type.shape
        referenced_type = objectfifo_type.element_type

        object_fifo = ObjectFifoOp.from_referenced_type(
            producerTile, consumerTiles, name, elemNumber, referenced_type, shape
        )

        return object_fifo


@irdl_op_definition
class ObjectFIFOReleaseOp(IRDLOperation):
    name = "aie.objectfifo.release"

    port = prop_def(IntegerAttr[IntegerType])
    size = prop_def(IntegerAttr[IntegerType])
    objFifo_name = prop_def(SymbolRefAttr)

    def __init__(
        self,
        port: IntegerAttr[IntegerType],
        size: IntegerAttr[IntegerType],
        object_fifo: str | SymbolRefAttr,
    ):
        if isinstance(object_fifo, str):
            object_fifo = SymbolRefAttr(object_fifo)

        super().__init__(
            properties={"objFifo_name": object_fifo, "port": port, "size": size}
        )

    def print(self, printer: Printer):
        printer.print(
            " ",
            self.objFifo_name,
            f"({ObjectFifoPortEnum.from_int(self.port.value.data).value}, ",
            self.size.value.data,
            ")",
        )

    @classmethod
    def parse(cls, parser: Parser) -> ObjectFIFOReleaseOp:
        object_fifo = SymbolRefAttr(parser.parse_symbol_name())
        parser.parse_characters("(")
        port = parser.parse_str_enum(ObjectFifoPortEnum)
        parser.parse_characters(",")

        size = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)

        parser.parse_characters(")")

        return ObjectFIFOReleaseOp(
            IntegerAttr.from_int_and_width(port.get_int(), 32), size, object_fifo
        )


@irdl_op_definition
class ObjectFifoLinkOp(IRDLOperation):
    name = "aie.objectfifo.link"

    fifoIns = prop_def(ArrayAttr[SymbolRefAttr])
    fifoOuts = prop_def(ArrayAttr[SymbolRefAttr])
    src_offsets = prop_def(ArrayAttr[IntegerAttr[IntegerType]])
    dst_offsets = prop_def(ArrayAttr[IntegerAttr[IntegerType]])

    def __init__(
        self,
        fifoIns: ArrayAttr[SymbolRefAttr] | Sequence[SymbolRefAttr] | Sequence[str],
        fifoOuts: ArrayAttr[SymbolRefAttr] | Sequence[SymbolRefAttr] | Sequence[str],
        src_offsets: ArrayAttr[IntegerAttr[IntegerType]] | Sequence[int],
        dst_offsets: ArrayAttr[IntegerAttr[IntegerType]] | Sequence[int],
    ) -> None:
        # fifoIns
        if isa(fifoIns, Sequence[str]):
            fifoIns = ArrayAttr([SymbolRefAttr(val) for val in fifoIns])
        elif isa(fifoIns, Sequence[SymbolRefAttr]):
            fifoIns = ArrayAttr(fifoIns)
        fifoIns = cast(ArrayAttr[SymbolRefAttr], fifoIns)

        # fifoOuts
        if isa(fifoOuts, Sequence[str]):
            fifoOuts = ArrayAttr([SymbolRefAttr(val) for val in fifoOuts])
        elif isa(fifoOuts, Sequence[SymbolRefAttr]):
            fifoOuts = ArrayAttr(fifoOuts)
        fifoOuts = cast(ArrayAttr[SymbolRefAttr], fifoOuts)

        # src_offsets
        if isa(src_offsets, Sequence[int]):
            src_offsets = ArrayAttr(
                [IntegerAttr.from_int_and_width(val, 64) for val in src_offsets]
            )
        src_offsets = cast(ArrayAttr[IntegerAttr[IntegerType]], src_offsets)

        # dst_offsets
        if isa(dst_offsets, Sequence[int]):
            dst_offsets = ArrayAttr(
                [IntegerAttr.from_int_and_width(val, 64) for val in dst_offsets]
            )
        dst_offsets = cast(ArrayAttr[IntegerAttr[IntegerType]], dst_offsets)

        super().__init__(
            properties={
                "dst_offsets": dst_offsets,
                "fifoIns": fifoIns,
                "fifoOuts": fifoOuts,
                "src_offsets": src_offsets,
            },
        )

    def print(self, printer: Printer):
        printer.print(" [")
        printer.print_list(self.fifoIns.data, printer.print_attribute)
        printer.print("] -> [")
        printer.print_list(self.fifoOuts.data, printer.print_attribute)
        printer.print("]([")
        printer.print_list([str(x.value.data) for x in self.src_offsets], printer.print)
        printer.print("] [")
        printer.print_list([str(x.value.data) for x in self.dst_offsets], printer.print)
        printer.print("])")

    @classmethod
    def parse(cls, parser: Parser) -> ObjectFifoLinkOp:
        fifoIns = [
            x.data
            for x in parser.parse_comma_separated_list(
                Parser.Delimiter.SQUARE, parser.parse_symbol_name
            )
        ]
        parser.parse_punctuation("->")
        fifoOuts = [
            x.data
            for x in parser.parse_comma_separated_list(
                Parser.Delimiter.SQUARE, parser.parse_symbol_name
            )
        ]
        parser.parse_characters("(")
        src_offsets = cast(
            list[int],
            parser.parse_comma_separated_list(
                Parser.Delimiter.SQUARE, parser.parse_number
            ),
        )
        dst_offsets = cast(
            list[int],
            parser.parse_comma_separated_list(
                Parser.Delimiter.SQUARE, parser.parse_number
            ),
        )
        parser.parse_characters(")")
        return ObjectFifoLinkOp(fifoIns, fifoOuts, src_offsets, dst_offsets)


@irdl_op_definition
class PLIOOp(IRDLOperation):
    name = "aie.plio"

    col = attr_def(IntegerAttr[IntegerType])

    def __init__(self, col: IntegerAttr[IntegerType]):
        super().__init__(attributes={"col": col}, result_types=[IndexType()])


@irdl_op_definition
class PacketFlowOp(IRDLOperation):
    name = "aie.packet_flow"

    ID = attr_def(IntegerAttr[IntegerType])
    region = region_def()

    traits = traits_def(SingleBlockImplicitTerminator(EndOp))

    def __init__(self, ID: IntegerAttr[IntegerType], region: Region):
        super().__init__(attributes={"ID": ID}, regions=[region])

    def print(self, printer: Printer):
        printer.print("(", f"0x{self.ID.value.data:X}", ") ")
        printer.print_region(self.region)

    @classmethod
    def parse(cls, parser: Parser) -> PacketFlowOp:
        parser.parse_characters("(")
        id = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(")")
        region = parser.parse_region()

        return PacketFlowOp(id, region)


@irdl_op_definition
class PacketDestOp(IRDLOperation):
    name = "aie.packet_dest"

    bundle = attr_def(WireBundleAttr)
    channel = attr_def(IntegerAttr[IntegerType])

    tile = operand_def(IndexType())

    traits = traits_def(HasParent(PacketFlowOp))

    def __init__(
        self,
        bundle: WireBundleAttr,
        channel: IntegerAttr[IntegerType],
        tile: Operation | SSAValue,
    ):
        super().__init__(
            attributes={"bundle": bundle, "channel": channel}, operands=[tile]
        )

    def print(self, printer: Printer):
        printer.print("<")
        printer.print(self.tile)
        printer.print(", ")
        printer.print(self.bundle.data)
        printer.print(" : ")
        printer.print(self.channel.value.data)
        printer.print(">")

    @classmethod
    def parse(cls, parser: Parser) -> PacketDestOp:
        parser.parse_characters("<")
        tile = parser.parse_operand()
        parser.parse_characters(",")
        bundle_enum = WireBundleAttr.parse_parameter(parser)
        bundle = WireBundleAttr(bundle_enum)
        parser.parse_characters(":")
        channel = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(">")

        return PacketDestOp(bundle, channel, tile)


@irdl_op_definition
class PacketRulesOp(IRDLOperation):
    name = "aie.packetrules"

    sourceBundle = attr_def(WireBundleAttr)
    sourceChannel = attr_def(IntegerAttr[IntegerType])

    def __init__(
        self, sourceBundle: WireBundleAttr, sourceChannel: IntegerAttr[IntegerType]
    ):
        super().__init__(
            attributes={"sourceBundle": sourceBundle, "sourceChannel": sourceChannel}
        )


@irdl_op_definition
class PacketRuleOp(IRDLOperation):
    name = "aie.rule"

    mask = attr_def(IntegerAttr[IntegerType])
    value = attr_def(IntegerAttr[IntegerType])

    amsel = operand_def(IndexType())

    traits = traits_def(HasParent(PacketRulesOp))

    def __init__(
        self,
        mask: IntegerAttr[IntegerType],
        value: IntegerAttr[IntegerType],
        amsel: Operation | SSAValue,
    ):
        super().__init__(attributes={"mask": mask, "value": value}, operands=[amsel])


@irdl_op_definition
class PacketSourceOp(IRDLOperation):
    name = "aie.packet_source"

    bundle = attr_def(WireBundleAttr)
    channel = attr_def(IntegerAttr[IntegerType])
    tile = operand_def(IndexType())

    traits = traits_def(HasParent(PacketFlowOp))

    def __init__(
        self,
        bundle: WireBundleAttr,
        channel: IntegerAttr[IntegerType],
        tile: Operation | SSAValue,
    ):
        super().__init__(
            attributes={"bundle": bundle, "channel": channel}, operands=[tile]
        )

    def print(self, printer: Printer):
        printer.print("<")
        printer.print(self.tile)
        printer.print(", ")
        printer.print(self.bundle.data)
        printer.print(" : ")
        printer.print(self.channel.value.data)
        printer.print(">")

    @classmethod
    def parse(cls, parser: Parser) -> PacketSourceOp:
        parser.parse_characters("<")
        tile = parser.parse_operand()
        parser.parse_characters(",")
        bundle_enum = WireBundleAttr.parse_parameter(parser)
        bundle = WireBundleAttr(bundle_enum)
        parser.parse_characters(":")
        channel = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)
        parser.parse_characters(">")

        return PacketSourceOp(bundle, channel, tile)


@irdl_op_definition
class PutCascadeOp(IRDLOperation):
    name = "aie.putCascade"

    cascadeValue = operand_def(IntegerType(CASCADE_SIZE))

    traits = traits_def(HasParent(CoreOp))

    def __init__(self, cascadeValue: Operation | SSAValue):
        super().__init__(operands=[cascadeValue])


@irdl_op_definition
class PutStreamOp(IRDLOperation):
    name = "aie.putStream"

    channel = operand_def(i32)
    streamValue = operand_def(
        IntegerType(32, Signedness.SIGNLESS)
        or Float32Type
        or IntegerType(128, Signedness.SIGNLESS)
    )

    traits = traits_def(HasParent(CoreOp))

    def __init__(
        self, channel: Operation | SSAValue, streamValue: Operation | SSAValue
    ):
        super().__init__(operands=[channel, streamValue])


@irdl_op_definition
class ShimDMAAllocationOp(IRDLOperation):
    name = "aie.shimDMAAllocation"

    sym_name = attr_def(StringAttr)
    channelDir = attr_def(IntegerAttr[I32])
    channelIndex = attr_def(IntegerAttr[IntegerType])
    col = attr_def(IntegerAttr[IntegerType])

    traits = traits_def(HasParent(DeviceOp))

    def __init__(
        self,
        sym_name: StringAttr,
        channelDir: IntegerAttr[IntegerType],
        channelIndex: IntegerAttr[IntegerType],
        col: IntegerAttr[IntegerType],
    ):
        super().__init__(
            attributes={
                "sym_name": sym_name,
                "channelDir": channelDir,
                "channelIndex": channelIndex,
                "col": col,
            }
        )


@irdl_op_definition
class ShimSwitchBoxOp(IRDLOperation):
    name = "aie.shimswitchbox"

    col = attr_def(IntegerAttr[IntegerType])

    def __init__(self, col: IntegerAttr[IntegerType]):
        super().__init__(attributes={"col": col}, result_types=[IndexType()])


@irdl_op_definition
class UseLockOp(IRDLOperation):
    name = "aie.use_lock"

    value = opt_attr_def(IntegerAttr[IntegerType])
    action = attr_def(LockActionAttr)
    blocking = opt_attr_def(LockBlockingAttr)
    lock = operand_def(IndexType())

    def __init__(
        self,
        value: IntegerAttr[IntegerType] | None,
        action: LockActionAttr,
        blocking: LockBlockingAttr | None,
        lock: Operation | SSAValue,
    ):
        super().__init__(
            attributes={"value": value, "action": action, "blocking": blocking},
            operands=[lock],
        )

    def print(self, printer: Printer):
        printer.print("(")
        printer.print_operand(self.lock)
        printer.print(", ")
        printer.print(self.action.data)
        printer.print(", ")
        if self.value:
            printer.print(self.value.value.data)
        printer.print(")")

    @classmethod
    def parse(cls, parser: Parser) -> UseLockOp:
        parser.parse_characters("(")
        lock = parser.parse_operand()
        parser.parse_characters(",")
        action = LockActionAttr(LockActionAttr.parse_parameter(parser))

        value = None
        if parser.parse_optional_characters(","):
            value = IntegerAttr.from_int_and_width(parser.parse_integer(), 32)

        blocking = None
        if parser.parse_optional_characters(","):
            blocking = LockBlockingAttr(LockBlockingAttr.parse_parameter(parser))
        parser.parse_characters(")")

        return UseLockOp(value, action, blocking, lock)


@irdl_op_definition
class WireOp(IRDLOperation):
    name = "aie.wire"

    sourceBundle = attr_def(WireBundleAttr)
    destBundle = attr_def(WireBundleAttr)
    source = operand_def(IndexType())
    dest = operand_def(IndexType())

    def __init__(
        self,
        sourceBundle: WireBundleAttr,
        destBundle: WireBundleAttr,
        source: Operation | SSAValue,
        dest: Operation | SSAValue,
    ):
        super().__init__(
            attributes={"sourceBundle": sourceBundle, "destBundle": destBundle},
            operands=[source, dest],
        )


AIE = Dialect(
    "aie",
    [
        AMSelOp,
        BufferOp,
        TileOp,
        ConnectOp,
        CoreOp,
        DMABDOp,
        DMABDPACKETOp,
        DMAStartOp,
        DebugOp,
        DeviceOp,
        ExternalBufferOp,
        FlowOp,
        GetCascadeOp,
        GetStreamOp,
        LockOp,
        MasterSetOp,
        MemOp,
        MemTileDMAOp,
        NextBDOp,
        ObjectFifoAcquireOp,
        ObjectFifoRegisterExternalBuffersOp,
        ObjectFIFOSubviewAccessOp,
        ObjectFifoOp,
        ObjectFIFOReleaseOp,
        ObjectFifoLinkOp,
        PLIOOp,
        PacketDestOp,
        PacketFlowOp,
        PacketRuleOp,
        PacketRulesOp,
        PacketSourceOp,
        PutCascadeOp,
        PutStreamOp,
        ShimDMAOp,
        ShimMuxOp,
        ShimSwitchBoxOp,
        SwitchboxOp,
        UseLockOp,
        WireOp,
        EndOp,
    ],
    [
        BDDimLayoutArrayAttr,
        BDDimLayoutArrayArrayAttr,
        WireBundleAttr,
        ObjectFIFO,
        ObjectFIFOSubview,
    ],
)
