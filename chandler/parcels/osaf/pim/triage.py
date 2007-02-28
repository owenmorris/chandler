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
    
    # Triage status is used to set (and is changed by) the column cell, 
    # but is overridden for sorting by _sectionTriageStatus; the
    # 'Triage' toolbar button removes any _sectionTriageStatus attributes
    # to force re-sorting.
    triageStatus = schema.One(TriageEnum, initialValue=TriageEnum.now, 
                              indexed=True)
    _sectionTriageStatus = schema.One(TriageEnum)

    # For sorting by how recently the triage status values changed, 
    # we keep these attributes, which are the time (in seconds) of the last 
    # change to each, negated for proper order. They're updated automatically 
    # when the corresponding triage status value is changed, by 
    # setTriageStatus and setSectionTriageStatus, below.
    triageStatusChanged = schema.One(schema.Float)
    _sectionTriageStatusChanged = schema.One(schema.Float)
        
    def getSectionTriageStatus(self):
        result = self.getAttributeValue('_sectionTriageStatus', default=None)
        if result is None:
            result = self.triageStatus
        return result

    def setSectionTriageStatus(self, value):
        self._sectionTriageStatus = value

    sectionTriageStatus = schema.Calculated(
        TriageEnum,
        fset=setSectionTriageStatus,
        fget=getSectionTriageStatus,
        basedOn=(_sectionTriageStatus, triageStatus),
        doc="Calculated for temporary sectionTriageStatus, before "
            "user has purged")

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [triageStatus, triageStatusChanged],
        ),
    )

    def __init__(self, *args, **kw):
        triageStatus = kw.pop('triageStatus', None)
        super(Triageable, self).__init__(*args, **kw)
        if triageStatus is not None:
            self.triageStatus = triageStatus
        if not hasattr(self, 'triageStatusChanged'):
            self.setTriageStatusChanged()

    @schema.observer(triageStatus)
    def setTriageStatusChanged(self, op='set', attribute=None, when=None):
        """
        Update triageStatusChanged, which is the number of seconds since the
        epoch that triageStatus was changed, negated for proper sort order.
        As a schema.observer of triageStatus, it's called automatically, but
        can also be called directly to set a specific time:
           item.setTriageStatusChanged(when=someDateTime)
        """
        self._setChangedTime('triageStatusChanged', when=when)

    @schema.observer(_sectionTriageStatus)
    def setSectionTriageStatusChanged(self, op='set', attribute=None, when=None):
        """ Just like setTriageStatusChanged, but for the section triage status """
        self._setChangedTime('_sectionTriageStatusChanged', when=when)
            
    def _setChangedTime(self, attributeName, when=None):
        """
        Common code for setTriageStatusChanged and 
        setSectionTriageStatusChanged
        """
        # Don't if we're in the middle of sharing...
        if getattr(self, '_share_importing', False):
            return

        when = when or datetime.now(tz=ICUtzinfo.default)
        setattr(self, attributeName, -time.mktime(when.utctimetuple()))
        
    def purgeSectionTriageStatus(self):
        """ 
        If this item has section status that's overriding its triage
        status, purge it. 
        """
        for attr in ('_sectionTriageStatus', '_sectionTriageStatusChanged'):
            if hasattr(self, attr):
                delattr(self, attr)
        
    def reminderFired(self, reminder, when):
        """
        Override of C{Remindable.reminderFired}: sets triageStatus
        to now.
        """
        pending = super(Triageable, self).reminderFired(reminder, when)
        
        self.triageStatus = TriageEnum.now
        self.setTriageStatusChanged(when=when)
        
        return pending

