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


"""
Stuff related to the dashboard
"""

from __future__ import with_statement

from application import schema
from osaf import Preferences
from osaf.framework.blocks import (
    Block, Table,  wxTable,
    Styles)
from osaf import pim
from i18n import ChandlerMessageFactory as _
from chandlerdb.util.c import UUID
import wx
import logging

logger = logging.getLogger(__name__)

class DashboardPrefs(Preferences):

    showSections = schema.One(schema.Boolean, defaultValue = True)
    
class DashboardBlock(Table):
    """
    A block class for the Chandler Dashboard.

    This class works with the expectation that the delegate is the
    SectionedGridDelegate from the Sections module.
    """
    from osaf.framework.blocks.calendar.CalendarBlocks import MiniCalendar
    
    miniCalendar = schema.One(inverse=MiniCalendar.dashboardView,
                              defaultValue=None)

    # A few extra character styles
    sectionLabelCharacterStyle = schema.One(Styles.CharacterStyle)
    sectionCountCharacterStyle = schema.One(Styles.CharacterStyle)
    
    schema.addClouds(
        copying = schema.Cloud(
            byRef = [sectionLabelCharacterStyle, sectionCountCharacterStyle,
                     miniCalendar]
        )
    )

    def instantiateWidget (self):
        widget = wxTable (self.parentBlock.widget, 
                          Block.Block.getWidgetID(self),
                          characterStyle=getattr(self, "characterStyle", None),
                          headerCharacterStyle=getattr(self, "headerCharacterStyle", None))
        self.registerAttributeEditors(widget)
        return widget
    
    def render(self, *args, **kwds):
        super(DashboardBlock, self).render(*args, **kwds)

        if __debug__:
            from Sections import SectionedGridDelegate
            assert isinstance(self.widget, SectionedGridDelegate)

        view = self.itsView
        prefs = schema.ns('osaf.views.main', view).dashboardPrefs
        view.watchItem(self, prefs, 'onEnableSectionsPref')
        
    def onDestroyWidget(self, *args, **kwds):
        view = self.itsView
        prefs = schema.ns('osaf.views.main', view).dashboardPrefs
        view.unwatchItem(self, prefs, 'onEnableSectionsPref')
        
        super(DashboardBlock, self).onDestroyWidget(*args, **kwds)

    def onEnableSectionsPref(self, op, item, names):
        if 'showSections' in names:
            self.synchronizeWidget()

    def onTriageEvent(self, event):
        # Removed the forced-auto-triage to get rid of the extra messages
        # (in time for the message freeze). Will get rid of the remaining
        # vestiges shortly.
        autoTriageToo = False
        # Adding a couple of messages for the progress box that will also 
        # appear here shortly.
        progressBoxTitle = _(u"Triage Progress")
        progressBoxMessage1 = _(u"Triaging items...")
        progressBoxMessage2 = _(u"Updating indexes...")
        progressBoxMessage3 = _(u"Triaging recurring events...")
        progressBoxMessage4 = _(u"Saving...")
        progressBoxMessage5 = _(u"Triage error")
        progressBoxMessage6 = _(u"Unable to triage. See chandler.log for details.")
                
        #import hotshot
        #print 'triaging'
        #prof = hotshot.Profile('triage.log')
        #prof.runcall(self._onTriageEvent, event, autoTriageToo)
        #prof.close()
        #print 'done triaging'
    
    #def _onTriageEvent(self, event, autoTriageToo):        
        # Don't fire all the observers (until we're done, that is).
        recurringEventsToHandle = set()
        mastersToPurge = set()
        attrsToFind = ((pim.EventStamp.modificationFor.name, None),
                       ('_sectionTriageStatus', None))
        view = self.itsView
        with view.observersDeferred():
            with view.reindexingDeferred():
                for key in self.contents.iterkeys():
                    master, sectionTS = view.findValues(key, *attrsToFind)
                    mastersToPurge.add(master)
                    if autoTriageToo or sectionTS is not None:
                        item = view[key]
                        item.purgeSectionTriageStatus()
                        if autoTriageToo:
                            if item.hasLocalAttributeValue('doAutoTriageOnDateChange'):
                                del item.doAutoTriageOnDateChange
                        
                            if master is None:
                                item.setTriageStatus('auto')
                            
                        if master is not None:
                            recurringEventsToHandle.add(master)
                
                for master in mastersToPurge:
                    # don't let masters keep their _sectionTriageStatus, if
                    # they do it'll be inherited inappropriately by
                    # modifications                    
                    if isinstance(master, UUID):
                        if view.findValue(master, '_sectionTriageStatus', None):
                            view[master].purgeSectionTriageStatus()
                    elif hasattr(master, '_sectionTriageStatus'):
                        master.purgeSectionTriageStatus()
                        
        # (We do this outside the deferrals because this depends on the indexes...
        for master in recurringEventsToHandle:
            if isinstance(master, UUID):
                master = view[master]

            pim.EventStamp(master).updateTriageStatus(checkOccurrences=autoTriageToo)

    def activeViewChanged(self):
        if self.miniCalendar is not None:
            self.miniCalendar.activeViewChanged()
            self.miniCalendar.previewArea.activeViewChanged()
