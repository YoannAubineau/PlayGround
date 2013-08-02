"""Helpers functions and classes."""

import cPickle
import functools

from contextlib import closing
from datetime import datetime
from UserDict import UserDict


class FreeboxException(Exception):
    pass


class ExpirableCache(UserDict):

    def __init__(self, ttl):
        UserDict.__init__(self)
        self.ttl = ttl
        
    def __contains__(self, name):
        if name not in self.data:
            return False
        expiry_date, value = self.data[name]
        if expiry_date < datetime.now():
            del self[name]
            return False
        return True

    def __setitem__(self, name, value):
        expiry_date = datetime.now() + self.ttl
        self.data[name] = (expiry_date, value)

    def __getitem__(self, name):
        if name not in self:
            raise KeyError(name)
        expiry_date, value = self.data[name]
        return value


class Memoize(object):

    def __init__(self, ttl=None):
        self.cache = ExpirableCache(ttl) if ttl else dict

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = self.keyfunc(*args, **kwargs)
            if key not in self.cache:
                self.cache[key] = func(*args, **kwargs)
            return self.cache[key]
        return wrapper

    @staticmethod
    def keyfunc(*args, **kwargs):
        return cPickle.dumps((args, sorted(kwargs.iteritems())))


def save_file(filepath, fileobj, bufsize=1024):
    with closing(fileobj) as f1, open(filepath, 'wb') as f2:
        buf = f1.read(bufsize)
        while buf:
            f2.write(buf)
            buf = f1.read(1024)
