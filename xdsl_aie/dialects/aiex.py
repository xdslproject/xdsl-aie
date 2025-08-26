from collections.abc import Sequence
from typing import cast

from typing_extensions import Self
from xdsl.dialects.builtin import (
    BoolAttr,
    DenseArrayBase,
    IntegerAttr,
    IntegerType,
    MemRefType,
    StringAttr,
    SymbolRefAttr,
    i64,
)
from xdsl.ir import Dialect, Operation, Region, SSAValue
from xdsl.irdl import (
    AttrSizedOperandSegments,
    IRDLOperation,
    ParsePropInAttrDict,
    irdl_op_definition,
    operand_def,
    opt_prop_def,
    prop_def,
    region_def,
    result_def,
    traits_def,
    var_operand_def,
)
from xdsl.parser import IndexType, Parser
from xdsl.printer import Printer
from xdsl.traits import HasParent, NoTerminator
from xdsl.utils.hints import isa

from xdsl_aie.dialects.aie import DeviceOp


@irdl_op_definition
class DmaMemcpyNdOp(IRDLOperation):
    name = "aiex.npu.dma_memcpy_nd"

    memref = operand_def(MemRefType)

    offsets = var_operand_def(IntegerType)
    sizes = var_operand_def(IntegerType)
    strides = var_operand_def(IntegerType)

    id = prop_def(IntegerAttr[IntegerType])
    issue_token = prop_def(BoolAttr)
    metadata = prop_def(SymbolRefAttr)

    irdl_options = [AttrSizedOperandSegments(as_property=True)]

    static_offsets = prop_def(DenseArrayBase)
    static_sizes = prop_def(DenseArrayBase)
    static_strides = prop_def(DenseArrayBase)

    def __init__(
        self,
        memref: SSAValue | Operation,
        static_offsets: Sequence[int] | DenseArrayBase,
        static_sizes: Sequence[int] | DenseArrayBase,
        static_strides: Sequence[int] | DenseArrayBase,
        metadata: str | StringAttr | SymbolRefAttr,
        id: int | IntegerAttr[IntegerType],
        issue_token: bool | BoolAttr,
        offsets: Sequence[SSAValue | Operation] = [],
        sizes: Sequence[SSAValue | Operation] = [],
        strides: Sequence[SSAValue | Operation] = [],
    ):
        if isa(static_offsets, Sequence[int]):
            static_offsets = DenseArrayBase.from_list(i64, static_offsets)
        static_offsets = cast(DenseArrayBase, static_offsets)
        if isa(static_sizes, Sequence[int]):
            static_sizes = DenseArrayBase.from_list(i64, static_sizes)
        static_sizes = cast(DenseArrayBase, static_sizes)
        if isa(static_strides, Sequence[int]):
            static_strides = DenseArrayBase.from_list(i64, static_strides)
        static_strides = cast(DenseArrayBase, static_strides)
        if not isinstance(metadata, SymbolRefAttr):
            metadata = SymbolRefAttr(metadata)
        if isinstance(id, int):
            id = IntegerAttr(id, i64)
        if isinstance(issue_token, bool):
            issue_token = IntegerAttr.from_bool(issue_token)

        super().__init__(
            operands=[memref, offsets, sizes, strides],
            properties={
                "id": id,
                "issue_token": issue_token,
                "metadata": metadata,
                "static_offsets": static_offsets,
                "static_sizes": static_sizes,
                "static_strides": static_strides,
            },
        )

        pass

    def print(self, printer: Printer):
        printer.print_string("(")
        printer.print_operand(self.memref)
        for static_operands in (
            self.static_offsets,
            self.static_sizes,
            self.static_strides,
        ):
            values = ", ".join([str(x) for x in static_operands.get_values()])
            printer.print_string(f"[{values}]")
        for other_operands in (self.offsets, self.sizes, self.strides):
            if other_operands:
                printer.print_string(", ")
                printer.print_operands(other_operands)
        printer.print_string(") ")
        printer.print_attr_dict(
            {"id": self.id, "issue_token": self.issue_token, "metadata": self.metadata}
        )
        printer.print_string(" : ")
        printer.print_attribute(self.memref.type)

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        parser.parse_punctuation("(")
        memref = parser.parse_operand()
        static_offsets = parser.parse_comma_separated_list(
            parser.Delimiter.SQUARE, parser.parse_integer
        )
        static_sizes = parser.parse_comma_separated_list(
            parser.Delimiter.SQUARE, parser.parse_integer
        )
        static_strides = parser.parse_comma_separated_list(
            parser.Delimiter.SQUARE, parser.parse_integer
        )
        parser.parse_punctuation(")")
        attrs = parser.parse_optional_dictionary_attr_dict()
        assert isinstance(metadata := attrs["metadata"], SymbolRefAttr)
        assert isa(id := attrs["id"], IntegerAttr[IntegerType])
        assert isa(issue_token := attrs["issue_token"], BoolAttr)
        parser.parse_punctuation(":")
        parser.parse_type()  # memref type

        return cls(
            memref,
            static_offsets,
            static_sizes,
            static_strides,
            metadata,
            id,
            issue_token,
        )


@irdl_op_definition
class DmaWaitOp(IRDLOperation):
    name = "aiex.npu.dma_wait"

    symbol = prop_def(SymbolRefAttr)

    irdl_options = [ParsePropInAttrDict()]

    assembly_format = "attr-dict"

    def __init__(self, symbol: str | StringAttr | SymbolRefAttr):
        if not isinstance(symbol, SymbolRefAttr):
            symbol = SymbolRefAttr(symbol)

        super().__init__(properties={"symbol": symbol})


@irdl_op_definition
class RuntimeSequenceOp(IRDLOperation):
    name = "aiex.runtime_sequence"

    sym_name = opt_prop_def(StringAttr)

    body = region_def()

    traits = traits_def(HasParent(DeviceOp), NoTerminator())

    def __init__(self, body: Region, name: StringAttr | str | None = None):
        if isinstance(name, str):
            name = StringAttr(name)

        super().__init__(properties={"sym_name": name}, regions=[body])

    def print(self, printer: Printer):
        if self.sym_name:
            printer.print_string(" @" + self.sym_name.data)
        printer.print_string("(")
        if self.body.blocks:
            printer.print_list(self.body.blocks[0].args, printer.print_block_argument)
        printer.print_string(") ")
        printer.print_region(
            self.body, print_entry_block_args=False, print_empty_block=False
        )

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        name = parser.parse_optional_symbol_name()
        parser.parse_characters("(")
        args: list[Parser.Argument] | None = []
        while True:
            if arg := parser.parse_optional_argument():
                args.append(arg)
            if not parser.parse_optional_punctuation(","):
                break
        parser.parse_characters(")")
        if not len(args):
            args = None
        region = parser.parse_region(args)
        return cls(body=region, name=name)


@irdl_op_definition
class DmaConfigureTaskOp(IRDLOperation):
    name = "aiex.dma_configure_task"

    tile = operand_def(IndexType)
    result = result_def(IndexType)

    body = region_def()

    direction = prop_def(IntegerAttr[IntegerType])  # TODO: fix for DMAChannelDirAttr
    channel = prop_def(IntegerAttr[IntegerType])
    issue_token = opt_prop_def(BoolAttr)
    repeat_count = opt_prop_def(IntegerAttr[IntegerType])

    traits = traits_def(HasParent(RuntimeSequenceOp))

    def __init__(
        self,
        tile: SSAValue | Operation,
        direction: int | IntegerAttr[IntegerType],
        channel: int | IntegerAttr[IntegerType],
        issue_token: bool | BoolAttr | None = None,
        repeat: int | IntegerAttr[IntegerType] | None = None,
    ):
        if isinstance(direction, int):
            direction = IntegerAttr.from_int_and_width(direction, 32)
        if isinstance(channel, int):
            channel = IntegerAttr.from_int_and_width(channel, 32)
        if isinstance(issue_token, bool):
            issue_token = IntegerAttr.from_int_and_width(int(issue_token), 1)
        if isinstance(repeat, int):
            repeat = IntegerAttr.from_int_and_width(repeat, 32)

        super().__init__(
            operands=[tile],
            properties={
                "direction": direction,
                "channel": channel,
                "issue_token": issue_token,
                "repeat": repeat,
            },
            result_types=[IndexType()],
        )


@irdl_op_definition
class DmaStartTaskOp(IRDLOperation):
    name = "aiex.dma_start_task"

    task = operand_def(IndexType)

    def __init__(self, task: SSAValue | Operation):
        super().__init__(operands=[task])


@irdl_op_definition
class DmaAwaitTaskOp(IRDLOperation):
    name = "aiex.dma_await_task"

    task = operand_def(IndexType)

    def __init__(self, task: SSAValue | Operation):
        super().__init__(operands=[task])


AIEX = Dialect(
    "aiex",
    [
        DmaMemcpyNdOp,
        DmaWaitOp,
        RuntimeSequenceOp,
        DmaConfigureTaskOp,
        DmaStartTaskOp,
        DmaAwaitTaskOp,
    ],
    [],
)
