from .job import find_job, jobs
from .proc import Process

import os
import sys


_flags = {}
_flags['tracebacks'] = False
_lastdir = os.getcwd()
_pushdirs = []


def builtin_cd(argv): 
    if argv[0] == 'popd':
        goto = _pushdirs[-1]
    elif len(argv) == 1:
        goto = os.path.expanduser('~')
    elif argv[1] == '-':
        goto = _lastdir
        print(goto)
    else:
        goto = argv[1]

    ld = os.getcwd()
    os.chdir(os.path.expanduser(goto))
    _lastdir = ld
    return 0

def builtin_exit(argv):
    raise EOFError

def builtin_bg(argv):
    if len(argv) == 1:
        job = find_job()
    else:
        try:
            job_id = int(argv[1])
        except ValueError:
            raise RuntimeError('invalid job id')
        job = find_job(job_id=job_id)
    job.continue_job(fg=False)
    return 0

def builtin_fg(argv):
    if len(argv) == 1:
        job = find_job()
    else:
        try:
            job_id = int(argv[1])
        except ValueError:
            raise RuntimeError('invalid job id')
        job = find_job(job_id=job_id)
    job.continue_job(fg=True)
    return 0

def builtin_jobs(argv):
    for job in jobs():
        if job.next is None: # ignore the jobs command
            break
        job.print_info()
    return 0

def builtin_pushd(argv):
    cwd = os.getcwd()
    builtin_cd(argv)
    _pushdirs.append(cwd)
    print(argv[1], ' '.join(reversed(_pushdirs)))
    return 0

def builtin_popd(argv):
    if len(_pushdirs) == 0:
        raise RuntimeError('directory stack empty')
    builtin_cd(argv)
    print(' '.join(reversed(_pushdirs)))
    _pushdirs.pop()
    return 0

def builtin_set(argv):
    if len(argv) != 3 or argv[1] not in ('enable', 'disable'):
        raise RuntimeError('required usage: set [enable|disable] [flag]')
    if argv[2] not in _flags:
        raise RuntimeError('{} not a valid flag'.format(argv[2]))
    _flags[argv[2]] = (argv[1] == 'enable')
    return 0


class Builtin_Process(Process):
    __slots__ = ('argv', 'pid', 'completed', 'stopped', 'status', 'term_signal')

    def __init__(self, argv):
        super().__init__(argv)

    def launch(self, pgid, infile, outfile, errfile, fg, subshell=False):
        builtinname = 'builtin_{}'.format(self.argv[0])
        func = globals().get(builtinname)

        if not subshell:
            try:
                func(self.argv)
            except Exception as e:
                print('pysh: {}: {}'.format(self.argv[0], str(e)), file=sys.stderr)
                self.mark_status(1)
            else:
                self.mark_status(0)
        else:
            super().launch(pgid, infile, outfile, errfile, fg)

    def _launch(self):
        sys.exit(func(self.argv))

