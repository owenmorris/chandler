
import os, errno

try:
    from fcntl import lockf, LOCK_SH, LOCK_EX, LOCK_NB, LOCK_UN

except ImportError:

    # If fcntl is not available, we must be on Windows,
    # so emulate the above fcntl symbols using msvcrt

    import msvcrt

    LOCK_SH = 0x01
    LOCK_EX = 0x02
    LOCK_NB = 0x04
    LOCK_UN = 0x08

    _locks = LOCK_SH | LOCK_EX | LOCK_NB
    
    _modes = [   # Translate Posix lock flags to msvcrt flags
        None,               # 0 = no-op
        msvcrt.LK_RLCK,     # 1 = LOCK_SH
        msvcrt.LK_LOCK,     # 2 = LOCK_EX
        None,               # 3 = Error
        None,               # 4 = Error
        msvcrt.LK_NBRLCK,   # 5 = LOCK_SH+LOCK_NB
        msvcrt.LK_NBLCK,    # 6 = LOCK_EX+LOCK_NB
        None,               # 7 = Error       
    ]

    def lockf(fileno,mode):
        if mode & LOCK_UN:
            msvcrt.locking(fileno, msvcrt.LK_UNLCK, 0)
        if mode & _locks:
            msmode = _modes[mode & _locks]
            if msmode is None:
                raise AssertionError("Invalid lock flags", mode)
            msvcrt.locking(fileno, msmode, 0)


def open(file):
    return os.open(file, os.O_CREAT | os.O_RDWR)

def close(file):
    return os.close(file)

# Locks don't upgrade or downgrade on Windows, therefore this function has
# to be called with LOCK_UN in combination with a lock flag to fake
# upgrading or downgrading of locks.

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
