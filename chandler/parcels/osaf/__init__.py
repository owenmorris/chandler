# List of modules/packages that are usable as "APIs" by scripting and
# development tools
# 

# When you uncomment this, make sure you list EVERYTHING that is supposed to be
# public. Otherwise things like epydoc think that everything that is not listed
# is private and will not provide documentation for it.
#__all__ = ['startup']

class ChandlerException(Exception):
    __slots__ = ['message', "exception", 'debugMessage']

    def __init__(self, message, exception=None, debugMessage=None):
        assert message is not None

        self.message = unicode(message)
        self.debugMessage = debugMessage
        self.exception = exception

    def __str__(self):
        if self.debugMessage is not None:
            return self.debugMessage

        return self.message.encode("utf-8")

    def __unicode__(self):
        return self.message
