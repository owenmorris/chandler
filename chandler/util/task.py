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
from chandlerdb.persistence.RepositoryError import MergeError
from osaf import sharing, activity

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

        def _failure(f):
            if not f.check(activity.ActivityAborted):
                logger.error("Task failed:\n%s\n", f.getTraceback())

            summary, extended = sharing.errors.formatFailure(f)
            err = f.value
            if not isinstance(err, Exception):
                err = f.type(f.value)
            self.callInMainThread(self.error, (err, summary, extended),
                                  done=True)

            return f

        def _success(result):
            self.callInMainThread(self.success, result, done=True)
            return result
        
        def _cleanup(what):
            if self.shutdownDeferred:
                self.shutdownDeferred.callback(None)
            reactor.removeSystemEventTrigger(triggerID)
            
            return what

        defer.maybeDeferred(self.run).addCallback(
            _success).addErrback(
            _failure).addBoth(
            _cleanup)
        
            
                




    def shutdownCallback(self):
        self.shutdownDeferred = defer.Deferred()
        self.cancelRequested = True
        self.shutdownInitiated()
        return self.shutdownDeferred

    def callInMainThread(self, f, arg, done=False):
        if self.running:
            def mainCallback(x):
                if self.running:
                    if done: self.running = False
                    f(x)
            wx.GetApp().PostAsyncEvent(mainCallback, arg)

    def _error(self, arg):
        self.callInMainThread(self.error, arg, done=True)

    def _success(self, result):
        self.callInMainThread(self.success, result, done=True)
