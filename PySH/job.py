from .term import Terminal

import errno
import os
import signal
import sys


_terminal = Terminal()


_first_job = None
_job_id = 1
_last_found_job_id = 1


def jobs():
    job = _first_job
    while job:
        yield job
        job = job.next

def add_job(job):
    global _job_id
    global _first_job

    job.job_id = _job_id
    _job_id += 1

    if _first_job is None:
        _first_job = job
    else:
        j = _first_job
        while j.next:
            j = j.next
        j.next = job

def remove_job(job):
    global _first_job
    global _job_id

    last = None
    for j in jobs():
        if j is job:
            if last:
                last.next = job.next
            else:
                _first_job = job.next
        last = j

    if _first_job is None:
        _job_id = 1

def find_job(pgid=None, job_id=None):
    global _last_found_job_id

    if pgid is None and job_id is None:
        job_id = _last_found_job_id
    for job in jobs():
        if (pgid and job.pgid == pgid) or (job_id and job.job_id == job_id):
            if job_id:
                _last_found_job_id = job_id
            return job

def find_process(pid):
    if pid == 0:
        return 
    for job in jobs():
        for proc in job.procs:
            if proc.pid == pid:
                return proc

def update_status():
    try:
        while True:
            pid, status = os.waitpid(-1, 3) # WAIT_ANY, WUNTRACED|WNOHANG
            proc = find_process(pid)
            if proc:
                proc.mark_status(status)
            else:
                break
    except OSError as e:
        if e.errno is not errno.ECHILD:
            raise

def notify():
    update_status()
    for job in jobs():
        if job.completed:
            if not job.notified:
                job.print_info()
                job.notified = True
            remove_job(job)
        elif job.stopped and not job.notified:
            job.print_info()
            job.notified = True


class Job:
    __slots__ = ('next', 'job_id', 'cmdline', 'procs', 'pgid', 'notified', 'tmodes', 'stdin', 'stdout', 'stderr')

    def __init__(self, cmdline):
        self.next = None
        self.cmdline = cmdline
        self.procs = []
        self.pgid = 0
        self.stdin = sys.stdin.fileno()
        self.stdout = sys.stdout.fileno()
        self.stderr = sys.stderr.fileno()
        self.notified = False
        self.tmodes = None

    @property
    def stopped(self):
        return all((p.completed or p.stopped for p in self.procs))

    @property
    def completed(self):
        return all((p.completed for p in self.procs))

    @property
    def terminated(self):
        return any((proc.term_signal for proc in self.procs))

    def add_proc(self, proc):
        self.procs.append(proc)

    def launch(self, fg=True):
        infile = self.stdin

        for procidx, proc in enumerate(self.procs):
            if (len(self.procs) - procidx) > 1:
                rfd, outfile = os.pipe()
            else:
                rfd = self.stdin
                outfile = self.stdout

            pid = proc.launch(self.pgid, infile, outfile, self.stderr, fg)

            if pid is None: # builtin
                pass
            else:
                proc.pid = pid
                if _terminal.interactive:
                    if self.pgid == 0:
                        self.pgid = pid
                    os.setpgid(pid, self.pgid)

                if infile != self.stdin:
                    os.close(infile)
                if outfile != self.stdout:
                    os.close(outfile)
                infile = rfd

                if not _terminal.interactive and fg:
                    self.wait()
                elif fg:
                    self._foreground()
                else:
                    self.print_info(short=True)
                    self._background()

            if fg and self.completed:
                self.notified = True

    def continue_job(self, fg = True):
        self._mark_running()
        if fg:
            self._foreground(True)
        else:
            self._background(True)

    def wait(self):
        try:
            while True:
                pid, status = os.waitpid(-1, 2) # WAIT_ANY, WUNTRACED
                proc = find_process(pid)
                if proc:
                    proc.mark_status(status)
                    if self.stopped or self.completed:
                        break
                else:
                    break
        except OSError as e:
            if e.errno is not errno.ECHILD:
                raise

    def print_info(self, short=False):
        if short:
            assert(len(self.procs) > 0)
            print('[{}] {}'.format(self.job_id, self.procs[-1].pid), file=sys.stderr)
        else:
            if self.completed:
                if self.terminated:
                    status = 'Terminated'
                else:
                    status = 'Done'
            elif self.stopped:
                status = 'Stopped'
            else:
                status = 'Running'
            print('[{}]\t{}\t\t{}'.format(self.job_id, status, self.cmdline), file=sys.stderr)

    def _mark_running(self):
        for proc in self.procs:
            proc.stopped = False
        self.notified = False

    def _foreground(self, cont=False):
        _terminal.grab_control(self.pgid)
        if cont:
            if self.tmodes:
                _terminal.restore_attributes(self.tmodes)
            os.kill(-self.pgid, signal.SIGCONT)
        self.wait()
        _terminal.grab_control(_terminal.shell_pgid)
        self.tmodes = _terminal.restore_attributes()

    def _background(self, cont=False):
        if cont:
            os.kill(-self.pgid, signal.SIGCONT)

