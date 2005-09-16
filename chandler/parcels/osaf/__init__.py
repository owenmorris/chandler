# List of modules/packages that are usable as "APIs" by scripting and
# development tools
# 
__all__ = ['startup']

class ChandlerException(Exception):
    __slots__ = ['message', 'debugMessage']

    def __init__(self, message, debugMessage=None):
        assert message is not None

        self.message = unicode(message)
        self.debugMessage = debugMessage

    def __str__(self):
        if self.debugMessage is not None:
            return self.debugMessage

        return self.message.encode("utf-8")

    def __unicode__(self):
        return self.message
