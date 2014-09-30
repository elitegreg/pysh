from signal import *

_saved = {}


def default_signals():
    for i in (SIGINT, SIGQUIT, SIGTSTP, SIGTTIN, SIGTTOU, SIGCHLD):
        _saved[i] = signal(i, SIG_DFL)

def ignore_signals():
    for i in (SIGQUIT, SIGTSTP, SIGTTIN, SIGTTOU):
        _saved[i] = signal(i, SIG_IGN)

def restore_signals(signo):
    signal(signo, _saved[signo])

