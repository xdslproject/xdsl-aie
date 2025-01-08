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
    irdl_op_definition,
    operand_def,
    opt_prop_def,
    prop_def,
    region_def,
    traits_def,
    var_operand_def,
)
from xdsl.parser import Parser
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

    x = prop_def(IntegerAttr[IntegerType])
    y = prop_def(IntegerAttr[IntegerType])


    def __init__(
        self,
        x: int | IntegerAttr[IntegerType],
        y: int | IntegerAttr[IntegerType],
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
        if isinstance(x, int):
            x = IntegerAttr(x, i64)
        if isinstance(y, int):
            y = IntegerAttr(y, i64)
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
                "x": x,
                "y": y,
            },
        )

        pass

    def print(self, printer: Printer):
        printer.print_string(f"({self.x.value.data}, {self.y.value.data}, ")
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
        x = parser.parse_integer()
        parser.parse_punctuation(",")
        y = parser.parse_integer()
        parser.parse_punctuation(",")
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
            x,
            y,
            memref,
            static_offsets,
            static_sizes,
            static_strides,
            metadata,
            id,
            issue_token,
        )


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


AIEX = Dialect(
    "aiex",
    [
        DmaMemcpyNdOp,
        RuntimeSequenceOp,
    ],
    [],
)
