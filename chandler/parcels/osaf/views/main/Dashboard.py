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
        #import hotshot
        #print 'triaging'
        #prof = hotshot.Profile('triage.log')
        #prof.runcall(self._onTriageEvent, event)
        #prof.close()
        #print 'done triaging'
    
    #def _onTriageEvent(self, event):        
        recurringEventsToHandle = set()
        itemsToPurge = set()
        view = self.itsView
        attrsToFind = ((pim.EventStamp.modificationFor.name, None),
                       ('_sectionTriageStatus', None))
        for key in self.contents.iterkeys():
            master, sectionTS = view.findValues(key, *attrsToFind)
            if sectionTS is not None:
                itemsToPurge.add(key)
            if master is not None:
                if sectionTS is not None:
                    itemsToPurge.add(master)
                recurringEventsToHandle.add(master)
        
        # Are there enough to need a progress dialog?
        # PPC Macs are slower than everything else.
        progressBoxThreshold = 500 if getPlatformID() == "osx-ppc" else 250    
        # We triage ordinary events much faster than recurring series
        recurringEventTriageScale = 10 # recurring events cost more

        totalWork = (len(recurringEventsToHandle) * recurringEventTriageScale) \
                    + len(itemsToPurge)
        showBox = totalWork > progressBoxThreshold
        if __debug__:
            logger.debug("Triaging %d items, %d recurrence masters: %sshowing progress box.",
                         len(itemsToPurge), len(recurringEventsToHandle),
                         "" if showBox else "NOT ")
        if showBox:
            from osaf.activity import Activity, ActivityAborted
            from application.dialogs import Progress
    
            activity = Activity(_(u"Triage Progress"))
            self.mainFrame = Progress.Show(activity)
            # (add 10% to the work to cover the commit time, and 5% for
            # reindexing)
            activity.started(msg=_(u"Triaging items..."),
                             totalWork=int(totalWork * 1.2))
            activityUpdate = activity.update
            activityCompleted = activity.completed
            activityFailed = activity.failed
            activityAborted = lambda: activity.abortRequested
        else:
            activityUpdate = activityCompleted = \
                activityFailed = activityAborted = \
                    lambda **dict: False

        try:
            # Purge all the ordinary items, while deferring indexing
            with view.observersDeferred():
                with view.reindexingDeferred():
                    for item in itemsToPurge:
                        if isinstance(item, UUID):
                            item = view[item]
                        item.purgeSectionTriageStatus()
                        activityUpdate(work=1)
                        if activityAborted():
                            break
                    if len(itemsToPurge) > 10:
                        activityUpdate(msg=_(u"Updating indexes..."))
            if not activityAborted():            
                # Purge all the recurrence masters. (We can't do this 
                # inside the deferrals because this depends on the indexes...)
                activityUpdate(msg=_(u"Triaging recurring events..."),
                               work=int(totalWork * 0.1)) # (made reindexing progress)
                for master in recurringEventsToHandle:
                    if isinstance(master, UUID):
                        master = view[master]
        
                    pim.EventStamp(master).updateTriageStatus()
                    activityUpdate(work=recurringEventTriageScale)
                    if activityAborted():
                        break

            # Commit now, while the box is still up.
            activityUpdate(msg=_(u"Saving..."))
            view.commit()
            activityUpdate(work=int(totalWork * 0.1))
            activityCompleted()            
        except Exception, e:
            logger.exception("Failed to triage")
            activityFailed(exception=e)
            msg = _(u"Unable to triage. See chandler.log for details.")
            dialog = wx.MessageDialog(None, msg,
                _(u"Triage error"), wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()


    def activeViewChanged(self):
        if self.miniCalendar is not None:
            self.miniCalendar.activeViewChanged()
            self.miniCalendar.previewArea.activeViewChanged()
