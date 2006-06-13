import wx
import logging
from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)

class Task(object):
    """
    Task class.

    @ivar running: Whether or not this task is actually running
    @type running: C{bool}

    """

    def __init__(self, view):
        super(Task, self).__init__()
        self.view = view

    def start(self, inOwnThread=False):
        """
        Launches an activity either in the twisted thread,
        or in its own background thread.

        @param inOwnThread: If C{True}, this activity runs in its
           own thread. Otherwise, it is launched in the twisted
           thread.
        @type inOwnThread: bool
        """

        from twisted.internet import reactor
        if inOwnThread:
            fn = reactor.callInThread
        else:
            fn = reactor.callFromThread

        fn(self.__threadStart)

    def __threadStart(self):
        # Run from background thread
        self.running = True

        try:
            result = self.run()
            self._success(result)
        except Exception, e:
            logger.exception("Task failed")
            self._error(e)

    def callInMainThread(self, f, arg, done=False):
        if self.running:
            def mainCallback(x):
                if self.running:
                    if done: self.running = False
                    f(x)
            wx.GetApp().PostAsyncEvent(mainCallback, arg)

    def _error(self, failure):
        self.view.cancel()
        self.callInMainThread(self.error, failure, done=True)

    def _success(self, result):
        self.view.commit()
        self.callInMainThread(self.success, result, done=True)
