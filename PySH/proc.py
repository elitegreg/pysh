from .signals import *
from .term import Terminal

import os
import sys


_terminal = Terminal()


class Process:
    __slots__ = ('argv', 'pid', 'completed', 'stopped', 'status', 'term_signal')

    def __init__(self, argv):
        self.argv = argv
        self.pid = None
        self.completed = False
        self.stopped = False
        self.status = None
        self.term_signal = None

    def launch(self, pgid, infile, outfile, errfile, fg):
        # TODO exception handling

        pid = os.fork()
        
        if pid == 0:
            if _terminal.interactive:
                pid = os.getpid()
                if pgid == 0:
                    pgid = pid
                os.setpgid(pid, pgid)
                if fg:
                   _terminal.grab_control(pgid)
                default_signals()
            if infile != sys.stdin.fileno():
                os.dup2(infile, sys.stdin.fileno())
            if outfile != sys.stdout.fileno():
                os.dup2(outfile, sys.stdout.fileno())
            if errfile != sys.stderr.fileno():
                os.dup2(errfile, sys.stderr.fileno())

            try:
                self._launch()
            except Exception as e:
                print('pysh: {}: {}'.format(self.argv[0], str(e)), file=sys.stderr)
            sys.exit(127)
        return pid

    def _launch(self):
        os.execvp(self.argv[0], self.argv)

    def mark_status(self, status):
        self.status = status
        if os.WIFSTOPPED(status):
            self.stopped = True
        else:
            self.completed = True
            if os.WIFSIGNALED(status):
                self.term_signal = os.WTERMSIG(status)

