from .borg import Borg

import os
import signal
import termios
import sys


class Terminal(Borg):
    def __init__(self):
        if not hasattr(self, '_Terminal__interactive'):
            self.__fd = sys.stdin.fileno()
            self.__interactive = sys.stdin.isatty()

    @property
    def interactive(self):
        return self.__interactive

    def loop_until_foreground(self, pgid):
        while os.tcgetpgrp(self.__fd) != pgid:
            os.kill(-pgid, signal.SIGTTIN)

    def grab_control(self, pgid):
        os.tcsetpgrp(self.__fd, pgid)

    def get_attributes(self):
        return termios.tcgetattr(self.__fd)

    def save_attributes(self):
        self.__attrs = self.get_attributes()

    def restore_attributes(self, attrs=None):
        if attrs is None:
            attrs = self.__attrs
        termios.tcsetattr(self.__fd, termios.TCSADRAIN, attrs)

