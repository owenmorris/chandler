
import os, errno
from fcntl import lockf, LOCK_SH, LOCK_EX, LOCK_NB, LOCK_UN


def open(file):
    return os.open(file, os.O_CREAT | os.O_RDWR)

def close(file):
    return os.close(file)

# Locks don't upgrade or downgrade on Windows, therefore this function has
# to be called with LOCK_UN in combination with a lock flag to fake
# upgrading or downgrading of locks. See lock.c for Windows version.

def lock(fileno, mode):
    if mode & ~LOCK_UN:
        try:
            lockf(fileno, mode & ~LOCK_UN)
            return True
        except IOError, e:
            if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
                return False
            raise
    elif mode & LOCK_UN:
        lockf(fileno, LOCK_UN)
        return True
