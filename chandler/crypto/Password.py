"""
Smart password classes.
"""

__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
_license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

class Password:
    """
    Password storage. Call clear() as soon as possible
    to remove the sensitive information from memory.
    """
    def __init__(self, password=None):
        """Create the password, either empty or initializing it with value."""
        if password:
            assert isinstance(password, str)
            self.__pw = list(password)
        else:
            self.__pw = []

    def __del__(self):
        if hasattr(self, '__pw'):
            self.clear()

    def clear(self):
        """Clear the password."""
        # XXX Is there any point in doing this in Python?
        for x in self.__pw:
            x = '0'
        self.__pw = []
        
    def set(self, password):
        """Set the password."""
        assert isinstance(password, str)
        self.clear()
        self.__pw = list(password)

    def __str__(self):
        """Get the password (as str)."""
        return ''.join(self.__pw)


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

    def _resetTimer(self):
        raise NotImplementedError

    def clear(self):
        """Clear the password."""
        super(TimeExpiringPassword, self).clear()
        self._resetTimer()
        
    def set(self, password, expire=600):
        """Set the password."""
        # XXX should I do instead?: assert expire > 0
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

    
#XXX Stupid name, any better ideas?
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
