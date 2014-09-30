from .ansi import *
from .builtins import _flags
from .cmd import parse_command
from .job import *
from .signals import *
from .term import Terminal
from .user import UserInfo

import os
import readline
import socket
import traceback


_terminal = Terminal()


class Shell:
    def __init__(self):
        self.__inputrc = os.path.join(os.path.expanduser('~'), '.inputrc')
        self.__histfile = os.path.join(os.path.expanduser('~'), '.pysh-history')

        if os.path.exists(self.__inputrc):
            readline.read_init_file(self.__inputrc)
        if os.path.exists(self.__histfile):
            readline.read_history_file(self.__histfile)

        self.__children = []

        self.__pid = os.getpid()

        if _terminal.interactive:
            _terminal.loop_until_foreground(os.getpgrp())
            ignore_signals()
            os.setpgid(self.__pid, self.__pid)
            _terminal.grab_control(self.__pid)
            _terminal.save_attributes()

        _terminal.shell_pgid = os.getpgid(self.__pid)

    def __enter__(self):
        return self

    def __exit__(self, exctype, excval, tb):
        readline.write_history_file(self.__histfile)

    def _prompt(self):
        info = UserInfo()
        ident = '{}{}@{}'.format(PROMPT_BRIGHT_GREEN, info.name, socket.gethostname())
        cwd = '{}{}{}'.format(PROMPT_BRIGHT_BLUE, info.subhomedir(os.getcwd()), PROMPT_RESET)
        return '{}:{}$ '.format(ident, cwd)

    def _dump_traceback(self):
        if _flags.get('tracebacks', False):
            print('Traceback:', file=sys.stderr)
            exctype, excval, tb = sys.exc_info()
            traceback.print_tb(tb)

    def run_cmd(self, cmd):
        try:
            cmd = parse_command(os.path.expandvars(cmd.strip()))
            cmd.run()
        except EOFError:
            return False
        return True

    def run_file(self, filename):
        with open(filename) as f:
            for line in f:
                self.run_cmd(line)

    def run_interactive(self):
        pyshrc = os.path.expanduser('~/.pyshrc')
        if os.path.exists(pyshrc):
            self.run_file(pyshrc)

        running = True

        while running:
            try:
                notify()
                running = self.run_cmd(input(self._prompt()))
            except KeyboardInterrupt:
                if _terminal.interactive:
                    print('^C')
            except EOFError:
                print('exit')
                return False

