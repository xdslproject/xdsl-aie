from xdsl.xdsl_opt_main import xDSLOptMain

from xdsl_aie.dialects import get_all_dialects
from xdsl_aie.transforms import get_all_passes


class xDSLAIEMain(xDSLOptMain):
    def register_all_passes(self):
        for name, pass_ in get_all_passes().items():
            self.register_pass(name, pass_)

    def register_all_dialects(self):
        for name, dialect in get_all_dialects().items():
            self.ctx.register_dialect(name, dialect)

    def register_all_targets(self):
        super().register_all_targets()


def main():
    xdsl_aie_main = xDSLAIEMain()
    xdsl_aie_main.run()


if "__main__" == __name__:
    main()
