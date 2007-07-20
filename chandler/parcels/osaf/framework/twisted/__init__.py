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

import thread, Queue, logging
import wx
import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.python.failure as failure
from twisted.python import threadable
from application import Globals

log = logging.getLogger(__name__)


def runInUIThread(func):
    """
    Decorator to ensure the function or method will be run on the UI thread.
    
    @warning: We will run on UI thread only if we have wx app object. Otherwise
              we'll call reactor.callFromThread, which is handy for testing.
              Evaluate your usage of this decorator to make sure this will not
              cause surprises in your use cases.
    """
    def decorate(*args, **kw):
        d = defer.Deferred()

        if thread.get_ident() == Globals.UI_Thread:
            try:
                d.callback(func(*args, **kw))
            except:
                d.errback()
        else:
            def callback():
                try:
                    result = func(*args, **kw)
                except:
                    f = failure.Failure()
                    reactor.callFromThread(d.errback, f)
                else:
                    reactor.callFromThread(d.callback, result)               
            
            try:
                postAsyncEvent = wx.GetApp().PostAsyncEvent
            except AttributeError:
                # See warning above.
                log.warning('runInUIThread not running on UI thread')
                reactor.callFromThread(callback)
            else:
                postAsyncEvent(callback)
        
        return d
    
    decorate.__name__ = func.__name__
    decorate.__dict__ = func.__dict__
    decorate.__doc__ = func.__doc__
    
    return decorate


def waitForDeferred(d):
    """
    Wait until deferred finishes and return the result.
    
    @note: Can not be run on twisted thread.
    """
    if threadable.isInIOThread():
        log.critical("Can't wait on twisted thread")
        raise RuntimeError("Can't wait on twisted thread")

    queue = Queue.Queue(1)
    d.addBoth(queue.put)
    result = queue.get(True)
    if isinstance(result, failure.Failure):
        result.raiseException()
    return result

