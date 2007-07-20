#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import wx
from twisted.internet import reactor, defer
import logging
from i18n import ChandlerMessageFactory as _
from repository.persistence.RepositoryError import MergeError
from osaf import sharing

logger = logging.getLogger(__name__)

class Task(object):
    """
    Task class.

    @ivar running: Whether or not this task is actually running
    @type running: C{bool}

    """

    def __init__(self, view=None):
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

        if inOwnThread:
            fn = reactor.callInThread
        else:
            fn = reactor.callFromThread

        fn(self.__threadStart)

    def __threadStart(self):
        # Run from background thread
        self.running = True

        self.shutdownDeferred = None
        triggerID = reactor.addSystemEventTrigger('before', 'shutdown',
            self.shutdownCallback)

        try:
            result = self.run()
            self._success(result)
        except Exception, e:
            logger.exception("Task failed")
            summary, extended = sharing.errors.formatException(e)
            self._error( (e, summary, extended) )

        if self.shutdownDeferred:
            self.shutdownDeferred.callback(None)

        reactor.removeSystemEventTrigger(triggerID)

    def shutdownCallback(self):
        self.shutdownDeferred = defer.Deferred()
        self.cancelRequested = True
        self.callInMainThread(self.shutdownInitiated, None, done=False)
        return self.shutdownDeferred

    def callInMainThread(self, f, arg, done=False):
        if self.running:
            def mainCallback(x):
                if self.running:
                    if done: self.running = False
                    f(x)
            wx.GetApp().PostAsyncEvent(mainCallback, arg)

    def _error(self, arg):
        if self.view is not None:
            self.view.cancel()
        self.callInMainThread(self.error, arg, done=True)

    def _success(self, result):

        def mergeFunction(code, item, attribute, value):
            if code == MergeError.ALIAS:
                key, currentKey, alias = value
                logger.warning("While merging attribute '%s' on %s, an alias conflict for key %s was detected: %s is set to the same alias: '%s'", attribute, item._repr_(), key, currentKey, alias)
                return alias + '_duplicate'
            raise NotImplementedError, (code, attribute, value)
        
        if self.view is not None:
            self.view.commit(mergeFunction)
        self.callInMainThread(self.success, result, done=True)
