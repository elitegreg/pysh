from .builtins import *
from .proc import Process


def create_proc(argv):
    cmd = argv[0]
    if 'builtin_{}'.format(cmd) in globals():
        return Builtin_Process(argv)
    return Process(argv)
