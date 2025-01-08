from collections.abc import Callable

from xdsl.ir import Dialect


def get_all_dialects() -> dict[str, Callable[[], Dialect]]:
    """Returns all available dialects."""

    def get_affine():
        from xdsl.dialects.affine import Affine

        return Affine

    def get_aie():
        from xdsl_aie.dialects.aie import AIE

        return AIE

    def get_aiex():
        from xdsl_aie.dialects.aiex import AIEX

        return AIEX

    def get_arith():
        from xdsl.dialects.arith import Arith

        return Arith

    def get_bufferization():
        from xdsl.dialects.bufferization import Bufferization

        return Bufferization

    def get_builtin():
        from xdsl.dialects.builtin import Builtin

        return Builtin

    def get_cf():
        from xdsl.dialects.cf import Cf

        return Cf

    def get_func():
        from xdsl.dialects.func import Func

        return Func

    def get_gpu():
        from xdsl.dialects.gpu import GPU

        return GPU

    def get_linalg():
        from xdsl.dialects.linalg import Linalg

        return Linalg

    def get_llvm():
        from xdsl.dialects.llvm import LLVM

        return LLVM

    def get_memref():
        from xdsl.dialects.memref import MemRef

        return MemRef

    def get_mpi():
        from xdsl.dialects.mpi import MPI

        return MPI

    def get_pdl():
        from xdsl.dialects.pdl import PDL

        return PDL

    def get_scf():
        from xdsl.dialects.scf import Scf

        return Scf

    def get_tensor():
        from xdsl.dialects.tensor import Tensor

        return Tensor

    def get_test():
        from xdsl.dialects.test import Test

        return Test

    def get_vector():
        from xdsl.dialects.vector import Vector

        return Vector

    return {
        "affine": get_affine,
        "aie": get_aie,
        "aiex": get_aiex,
        "arith": get_arith,
        "bufferization": get_bufferization,
        "builtin": get_builtin,
        "cf": get_cf,
        "func": get_func,
        "gpu": get_gpu,
        "linalg": get_linalg,
        "llvm": get_llvm,
        "memref": get_memref,
        "mpi": get_mpi,
        "pdl": get_pdl,
        "scf": get_scf,
        "tensor": get_tensor,
        "test": get_test,
        "vector": get_vector,
    }
