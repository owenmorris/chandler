"""
Smart password classes.
"""

__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
_license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

class Password(object):
    """
    Password storage. Call clear() as soon as possible
    to remove the sensitive information from memory.
    """
    def __init__(self, password=None):
        """Create the password, either empty or initializing it with value."""
        if password is not None:
            if not isinstance(password, str):
                raise TypeError, 'password must be string'
            self._pw = list(password)
        else:
            self._pw = []

    def __del__(self):
        if hasattr(self, '_pw'):
            self.clear()

    def clear(self):
        """Clear the password."""
        # XXX There probably isn't much point in doing this in Python,
        # XXX might want to do this in C instead.
        for x in self._pw:
            x = '0'
        self._pw = []
        
    def set(self, password):
        """Set the password."""
        if not isinstance(password, str):
            raise TypeError, 'password must be string'
        self.clear()
        self._pw = list(password)

    def __str__(self):
        """Get the password (as str)."""
        return ''.join(self._pw)


class PasswordExpiredException(Exception): pass


class TimeExpiringPassword(Password):
    """
    A password that clears itself after a set period of inactivity.
    """
    def __init__(self, password=None, expire=600):
        if expire <= 0:
            raise ValueError, 'expire value must be positive'
        super(TimeExpiringPassword, self).__init__(password)
        self._expire = expire
        self._hasExpired = False

    # XXX Need to implement actual timer that will cause auto clear
    # look how twisted does this, and our notification mgr
    # python cookbook might also have something

    def _resetTimer(self):
        raise NotImplementedError

    def clear(self):
        """Clear the password."""
        super(TimeExpiringPassword, self).clear()
        self._resetTimer()
        
    def set(self, password, expire=600):
        """Set the password."""
        if expire <= 0:
            raise ValueError, 'expire value must be positive'
        super(TimeExpiringPassword, self).set(password)
        self._resetTimer()
        self._expire = expire        

    def __str__(self):
        """Get the password (as str)."""
        if self._hasExpired:
            raise PasswordExpiredException, 'expire limit exceeded, password forgotten'
        self._resetTimer()
        return super(TimeExpiringPassword, self).__str__()

    
class AskUserAsNeededPassword(TimeExpiringPassword):
    """
    This password class will prompt the user to re-enter the password
    if it has expired.
    """
    def __str__(self):
        """Get the password (as str)."""
        try:
            return super(AskUserAsNeededPassword, self).__str__()
        except PasswordExpiredException:
            #XXX Prompt the user
            raise NotImplementedError
