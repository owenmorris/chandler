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

from __future__ import with_statement

import time
from application import schema
from datetime import datetime
from osaf.pim.reminders import Remindable
from i18n import ChandlerMessageFactory as _
from PyICU import ICUtzinfo

import logging
logger = logging.getLogger(__name__)


class TriageEnum(schema.Enumeration):
    values = { "now": 0 , "later": 5000, "done": 10000 }

triageStatusNames = { TriageEnum.now: _(u"Now"),
                      TriageEnum.later: _(u"Later"),
                      TriageEnum.done: _(u"Done")
                    }
def getTriageStatusName(value):
    return triageStatusNames[value]

# Bug 6525: the clicking sequence isn't the sort order
triageStatusClickSequence = { TriageEnum.now: TriageEnum.done,
                              TriageEnum.done: TriageEnum.later,
                              TriageEnum.later: TriageEnum.now }
def getNextTriageStatus(value):
    return triageStatusClickSequence[value]
    

class Triageable(Remindable):
    """ An item with triage status, in all its flavors"""
    
    # Notes:
    # 
    # - There are two sets of triage status attributes:
    #   - 'triageStatus' is used to set (and is changed by) the dashboard
    #     column cell and the detail view markup-bar button. It's also used
    #     for ordering in the dashboard unless there's this:
    #   - 'sectionTriageStatus' overrides triageStatus for sorting, if it
    #     exists; the 'Triage' toolbar button removes the sectionTriageStatus 
    #     attributes to force re-sorting by triageStatus alone.
    #
    # - Each actually consists of two attributes: the actual status attribute,
    #   and a timestamp (in UTC) that says how recently the attribute was
    #   changed; it's used for subsorting in each triage status section in the
    #   dashboard.
    #
    # - These attributes are generally set only by the setTriageStatus method,
    #   and read using the Calculated properties.
    #   which takes care of updating the timestamp attributes appropriately.
    #   The raw attributes are directly accessible if you want to avoid the
    #   magic (attn: sharing and recurrence :-) )
    
    _triageStatus = schema.One(TriageEnum, defaultValue=TriageEnum.now, 
                              indexed=True)
    _sectionTriageStatus = schema.One(TriageEnum)
    _triageStatusChanged = schema.One(schema.Float, defaultValue=None)
    _sectionTriageStatusChanged = schema.One(schema.Float)
    
    # Should we autotriage when the user changes a date or when an alarm fires?
    # Normally yes, so starts True; no once the user has manually set triage
    # status.
    # @@@ currently, never reset to yes; a post-Preview task will do this when
    # triage is set (either manually, or by the user) to the value it would have
    # if autotriaged... or something like that.
    doAutoTriageOnDateChange = schema.One(schema.Boolean, defaultValue=True)
    
    schema.addClouds(
        sharing = schema.Cloud(
            # To avoid compatibility issues with old shares, I didn't add
            # doAutoTriageOnDateChange to the sharing cloud -- this is all
            # going away soon anyway...
            literal = [_triageStatus, _triageStatusChanged],
        ),
    )

    schema.initialValues(
        _triageStatusChanged = lambda self: self.makeTriageStatusChangedTime()
    )
    
    @staticmethod
    def makeTriageStatusChangedTime(when=None):
        # get a float representation of a time from 'when' (or the current
        # time if when is None or not passed)
        if isinstance(when, float):
            pass # nothing to do
        elif isinstance(when, datetime):
            # (mktime wants local time, so make sure 'when' is 
            # in the local timezone)
            when = -time.mktime(when.astimezone(ICUtzinfo.default).timetuple())
        else:
            when = -time.time()
        return when

    def setTriageStatus(self, newStatus=None, when=None, 
                        pin=False, popToNow=False, force=False):
        """
        Set triageStatus to this value, and triageStatusChanged
        to 'when' if specified (or the current time if not).
        
        Newstatus can be 'auto' to autotriage this item based on its 
        inherent times (eg, startTime for an event, or alarm time if the
        item has one).
        
        If pin, save the existing triageStatus/triageStatusChanged
        in _sectionTriageStatus & _sectionTriageStatusChanged, which will
        have the effect of keeping the item in place in the dashboard until
        the next purge. (If there's already a _sectionTriageStatus value,
        don't overwrite it, unless force is True.)
        
        If popToNow, use _sectionTriageStatus/_sectionTriageStatusChanged
        to pop the item to the top of the Now section (again, only if force
        if the item already has section status).
        """
        # Don't autotriage unless the flag says we should.
        if newStatus == 'auto' and not self.doAutoTriageOnDateChange:
            from osaf.framework.blocks.Block import debugName
            logger.debug("Not Autotriaging %s", debugName(self))
            return

        # Don't reindex or notify until we're done with these changes
        with self.itsView.observersDeferred():
            with self.itsView.reindexingDeferred():
                # Manipulate section status if necessary
                if pin:
                    self.__setTriageAttributes(self._triageStatus,
                                               self._triageStatusChanged,
                                               True, force)
                elif popToNow:
                    from osaf.framework.blocks.Block import debugName
                    logger.debug("Popping %s to Now", debugName(self))
                    self.__setTriageAttributes(TriageEnum.now, None,
                                               True, force)
                    
                # Autotriage if we're supposed to.
                if newStatus == 'auto':
                    # Give our stamps a chance to autotriage
                    newStatus = None
                    from stamping import Stamp
                    for stampObject in Stamp(self).stamps:
                        # If the stamp object has an autoTriage method, and
                        # returns True when we call it, we're done.
                        method = getattr(type(stampObject), 'autoTriage', None)
                        if method is not None:
                            newStatus = method(stampObject)
                            if newStatus is not None:
                                if isinstance(newStatus, tuple):
                                    # The stamp specified a time too - note it.
                                    (newStatus, when) = newStatus
                                else:
                                    when = None
                                break
        
                    if newStatus is None:
                        # The stamps didn't do it; put ourself in Later if we 
                        # have a future reminder. Otherwise, leave things be.
                        reminder = self.getUserReminder()
                        if reminder is not None \
                           and reminder.nextPoll != reminder.farFuture \
                           and reminder.nextPoll > now:
                            from osaf.framework.blocks.Block import debugName
                            logger.debug("Autotriaging %s to LATER", 
                                         debugName(self))
                            newStatus = TriageEnum.later
                    
                # If we were given, or calculated, a triage status, set it.
                if newStatus is not None:
                    self.__setTriageAttributes(newStatus, when, False, True)

    triageStatus = schema.Calculated(
        TriageEnum,
        fget=lambda self: self._triageStatus,
        basedOn=(_triageStatus,))

    triageStatusChanged = schema.Calculated(
        schema.Float,
        fget=lambda self: self._triageStatusChanged,
        basedOn=(_triageStatusChanged,))

    sectionTriageStatus = schema.Calculated(
        TriageEnum,
        fget=lambda self: getattr(self, '_sectionTriageStatus',
                                  self._triageStatus),
        basedOn=(_sectionTriageStatus, _triageStatus),
        doc="Allow _sectionTriageStatus to override triageStatus")
            
    def __setTriageAttributes(self, newStatus, when, section, force):
        """
        Common code for setTriageStatus and setSectionTriageStatus
        """
        # Don't if we already have this attribute pair, unless we're forcing.
        tsAttr = '_sectionTriageStatus' if section else '_triageStatus'
        if not force and hasattr(self, tsAttr):
            return
        
        # Don't if we're in the middle of sharing...
        # @@@ I'm not sure if this is still necessary...
        if getattr(self, '_share_importing', False):
            return

        tscValue = Triageable.makeTriageStatusChangedTime(when)
        setattr(self, tsAttr, newStatus)
        tscAttr = '_sectionTriageStatusChanged' if section else '_triageStatusChanged'
        setattr(self, tscAttr, tscValue)
    
    def copyTriageStatusFrom(self, item):
        self._triageStatus = item._triageStatus
        if item._triageStatusChanged is not None:
            self._triageStatusChanged = item._triageStatusChanged
        if hasattr(item, '_sectionTriageStatus'):
            self._sectionTriageStatus = item._sectionTriageStatus
            stsc = getattr(item, '_sectionTriageStatusChanged', None)
            if stsc is not None:
                self._sectionTriageStatusChanged = stsc
        elif hasattr(self, '_sectionTriageStatus'):
            del self._sectionTriageStatus
            if hasattr(self, '_sectionTriageStatusChanged'):
                del self._sectionTriageStatusChanged
        self.doAutoTriageOnDateChange = item.doAutoTriageOnDateChange
            
    def purgeSectionTriageStatus(self):
        """ 
        If this item has section status that's overriding its triage
        status, purge it. 
        """
        for attr in ('_sectionTriageStatus', '_sectionTriageStatusChanged'):
            if hasattr(self, attr):
                delattr(self, attr)

    def resetAutoTriageOnDateChange(self):
        """
        The user changed triage status. Disable certain future automatic
        triaging
        
        @@@ Future: ... unless this change is to the status that the
        item would be triaged to if we autotriaged it now, in which
        case we re-enable future autotriaging.
        """
        self.doAutoTriageOnDateChange = False

    def reminderFired(self, reminder, when):
        """
        Override of C{Remindable.reminderFired}: sets triageStatus
        to now as of the time the reminder was due.
        """
        pending = super(Triageable, self).reminderFired(reminder, when)
        
        self.setTriageStatus(TriageEnum.now, when=when)
        self.resetAutoTriageOnDateChange()
        return pending

    if __debug__:
        def triageState(self):
            """ 
            For debugging, collect the triage status variables in a tuple 
            """
            def changedToDate(c):
                return None if c is None else time.asctime(time.gmtime(-c))
                
            return (getattr(self, '_triageStatus', None),
                    changedToDate(getattr(self, '_triageStatusChanged', None)),
                    getattr(self, '_sectionTriageStatus', None),
                    changedToDate(getattr(self, '_sectionTriageStatusChanged', None)),
                    getattr(self, 'doAutoTriageOnDateChange', None))
                    
