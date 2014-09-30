from .borg import Borg

import os
import pwd

class UserInfo(Borg):
    _state = {}
    
    def __new__(cls, *p, **k):
        self = object.__new__(cls, *p, **k)
        self.__dict__ = cls._state
        return self

    def __init__(self):
        self.__uid = os.geteuid()
        try:
            info = pwd.getpwuid(self.__uid)
            self.__name = info.pw_name
            self.__homedir = info.pw_dir
        except KeyError:
            self.__name = str(self.__uid)
            self.__homedir = os.getenv('HOME', '/')

    @property
    def name(self):
        return self.__name

    @property
    def homedir(self):
        return self.__homedir

    def subhomedir(self, path, sub='~'):
        if self.__homedir[-1] == '/' or not path.startswith(self.__homedir):
            return path
        return path.replace(self.__homedir, '~', 1)

