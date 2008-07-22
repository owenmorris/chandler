#   Copyright (c) 2003-2008 Open Source Applications Foundation
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
from osaf.framework.blocks import Block, Table,  wxTable, Styles
from osaf import pim
from osaf.sharing import isReadOnly
from i18n import ChandlerMessageFactory as _
from application.Utility import getPlatformID
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
        widget = wxDashboard(self.parentBlock.widget, 
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

    def onTriageEventUpdateUI(self, event):
        # cf Bug 11170: we are always enabled
        event.arguments['Enable'] = True

    def onTriageEvent(self, event):
        #import hotshot
        #print 'triaging'
        #prof = hotshot.Profile('triage.log')
        #prof.runcall(self._onTriageEvent, event)
        #prof.close()
        #print 'done triaging'
    
    #def _onTriageEvent(self, event):        
        if False:
            # Messages previously added to support a triage progress box
            boxTitle = _(u"Triage Progress")
            progress1 = _(u"Triaging items...")
            progress2 = _(u"Triaging recurring events...")
            progress3 = _(u"Saving...")
            failureMsg = _(u"Unable to triage. See chandler.log for details.")
            failureTitle = _(u"Triage Error")

        # Don't fire all the observers (until we're done, that is).
        recurringEventsToHandle = set()
        mastersToPurge = set()
        attrsToFind = ((pim.EventStamp.modificationFor.name, None),
                       ('_sectionTriageStatus', None),
                       ('_sectionTriageStatusChanged', None))
        view = self.itsView
        with view.observersDeferred():
            with view.reindexingDeferred():
                for key in self.contents.iterkeys():
                    master, sectionTS, sectionTSChanged = \
                        view.findValues(key, *attrsToFind)
                    hasSectionTS = sectionTS or sectionTSChanged
                    mastersToPurge.add(master)
                    if hasSectionTS:
                        item = view[key]
                        item.purgeSectionTriageStatus()
                            
                        if master is not None:
                            recurringEventsToHandle.add(master)
                
                for master in mastersToPurge:
                    # don't let masters keep their _sectionTriageStatus, if
                    # they do it'll be inherited inappropriately by
                    # modifications                    
                    if isinstance(master, UUID):
                        sectionTS, sectionTSChanged = view.findValues(master, 
                            ('_sectionTriageStatus', None),
                            ('_sectionTriageStatusChanged', None))
                        if sectionTS or sectionTSChanged:
                            view[master].purgeSectionTriageStatus()
                    elif hasattr(master, '_sectionTriageStatus') or \
                         hasattr(master, '_sectionTriageStatusChanged'):
                        master.purgeSectionTriageStatus()
                        
        # (We do this outside the deferrals because this depends on the indexes...
        for master in recurringEventsToHandle:
            if isinstance(master, UUID):
                master = view[master]

            pim.EventStamp(master).updateTriageStatus()
        
    def activeViewChanged(self):
        if self.miniCalendar is not None:
            self.miniCalendar.activeViewChanged()
            self.miniCalendar.previewArea.activeViewChanged()

    def onViewEventUpdateUI(self, event):
        event.arguments['Check'] = (event.viewTemplatePath == 'Dashboard')
            
class wxDashboard(wxTable):

    def OnItemDrag(self, event):
        if isReadOnly(self.blockItem.contentsCollection):
            event.Skip(False)
            wx.MessageBox(_(u'This collection is read-only. You cannot drag items out of read-only collections.'), _(u'Warning'), parent=self)
        else:
            return super(wxDashboard, self).OnItemDrag(event)
