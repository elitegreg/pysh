from .job import *
from .proc_factory import create_proc

import glob
import os
import string
import subprocess


def shellglob(x):
    result = glob.glob(x)
    if len(result) == 0:
        return [x]
    return result

def parse_command(cmdline):
    cmd = Command()
    cmd._parse(cmdline)
    return cmd


class Command:
    def __init__(self):
        self.__fg = True

    def _parse(self, cmd):
        state = None
        self.__parts = []
        token = []
        cmdline = []
        
        for i, c in enumerate(cmd):
            if state is None:
                if c in string.whitespace:
                    tok = shellglob(''.join(token))
                    for tok in shellglob(''.join(token)):
                        self.__parts.append(tok)
                        cmdline.extend(tok)
                        cmdline.append(c)
                    del token[:]
                    continue
                elif c in ('"', "'"):
                    state = c
                    continue
                elif c == '&':
                    self.__fg = False
                    break
            elif state in ('"', "'"):
                if c == state:
                    state = None
                    continue

            token.append(c)

        if token:
            for tok in shellglob(''.join(token)):
                self.__parts.append(tok)
                cmdline.extend(tok)
                cmdline.append(' ')
        self.__cmdline = ''.join(cmdline)

    def run(self):
        if len(self.__parts):
            proc = create_proc(self.__parts)
            job = Job(self.__cmdline)
            job.add_proc(proc)
            add_job(job)
            job.launch(fg=self.__fg)

