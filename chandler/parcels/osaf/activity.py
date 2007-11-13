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


"""Activity monitoring module"""

from chandlerdb.util.c import UUID
from osaf import ChandlerException
from i18n import ChandlerMessageFactory as _

import logging
logger = logging.getLogger(__name__)

__all__ = [
    'Activity',
    'ActivityAborted',
    'Listener',
    'STATUS_ABORTED',
    'STATUS_FAILED',
    'STATUS_INACTIVE',
    'STATUS_COMPLETE',
    'STATUS_ACTIVE',
]


class ActivityAborted(ChandlerException):
    """ Exception raised if an Activity is aborted """



STATUS_ABORTED    = -4
STATUS_FAILED     = -3
STATUS_INACTIVE   = -2
STATUS_COMPLETE   = -1
STATUS_ACTIVE     = 0

# STATUS_INACTIVE means the Activity object has been created, but work
# hasn't begun

# STATUS_ACTIVE means work is progressing, but the amount of work to perform
# is unknown

# A status between 1 and 99 is a percentage of work accomplished

# STATUS_COMPLETE means the activity is done




class Activity(object):

    def __init__(self, title):
        self.id = UUID()
        self.title = title
        self.status = STATUS_INACTIVE
        self.totalWork = None
        self.workDone = 0
        self.exception = None
        self.abortRequested = False

    def __repr__(self):
        return "Activity('%s', %d)" % (self.title, self.status)

    def started(self, *args, **kwds):
        self.status = STATUS_ACTIVE
        kwds['status'] = self.status
        self.abortRequested = False
        self.update(*args, **kwds)

    def completed(self):
        self.status = STATUS_COMPLETE
        Listener.broadcast(self, status=self.status)

    def failed(self, exception=None):
        self.status = STATUS_FAILED
        self.exception = exception
        Listener.broadcast(self, status=self.status, exception=exception)

    def aborted(self):
        self.status = STATUS_ABORTED
        Listener.broadcast(self, status=self.status)

    def update(self, *args, **kwds):

        computePercentage = False

        if 'totalWork' in kwds:
            # number of total units of work involved in the activity
            self.totalWork = kwds['totalWork']
            if self.totalWork is None:
                kwds['percent'] = None

        if 'workDone' in kwds:
            # allows direct setting of work done so far
            self.workDone = kwds['workDone']
            if self.totalWork:
                computePercentage = True

        if 'work' in kwds:
            # increments work done
            self.workDone += kwds['work']
            if self.totalWork:
                computePercentage = True

        if computePercentage:
            percent = min(int(self.workDone * 100 / self.totalWork), 100)
            kwds['percent'] = percent

        if self.abortRequested or Listener.broadcast(self, *args, **kwds):
            self.aborted()
            raise ActivityAborted(_(u"Cancelled by user."))

    def requestAbort(self):
        self.abortRequested = True



listeners = set()

class Listener(object):

    def __init__(self, callback=None, activity=None):
        self.callback = callback
        self.activity = activity
        self.register()

    def register(self):
        global listeners
        listeners.add(self)

    def unregister(self):
        global listeners
        listeners.remove(self)

    @classmethod
    def broadcast(cls, activity, *args, **kwds):
        abort = False
        for listener in list(listeners): # make a copy in case the set changes
            if (listener.callback and listener.activity in (None, activity)):
                # print "CALLING LISTENER", listener
                if listener.callback(activity, *args, **kwds):
                    abort = True
        return abort


# default stdout listener
def callback(activity, *args, **kwds):
    print activity, args, kwds

# listener = Listener(callback=callback)



def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'activity.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

