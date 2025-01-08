from typing import Self

from xdsl.dialects.builtin import StringAttr
from xdsl.ir import Dialect, Region
from xdsl.irdl import (
    IRDLOperation,
    irdl_op_definition,
    opt_prop_def,
    region_def,
    traits_def,
)
from xdsl.parser import Parser
from xdsl.printer import Printer
from xdsl.traits import HasParent, NoTerminator

from xdsl_aie.dialects.aie import DeviceOp


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
        RuntimeSequenceOp,
    ],
    [],
)
