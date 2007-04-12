#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
    Block, debugName, Table,  wxTable, GridCellAttributeEditor, 
    GridCellAttributeRenderer, Styles, BranchPoint)
from osaf.framework.attributeEditors import AttributeEditors
from osaf import pim
from i18n import ChandlerMessageFactory as _
from chandlerdb.util.c import UUID
import wx
import logging

logger = logging.getLogger(__name__)

if __debug__:
    evtNames = {
        wx.wxEVT_ENTER_WINDOW: 'ENTER_WINDOW',
        wx.wxEVT_LEAVE_WINDOW: 'LEAVE_WINDOW',
        wx.wxEVT_LEFT_DOWN: 'LEFT_DOWN',
        wx.wxEVT_LEFT_UP: 'LEFT_UP',
        wx.wxEVT_LEFT_DCLICK: 'LEFT_DCLICK',
        wx.wxEVT_MIDDLE_DOWN: 'MIDDLE_DOWN',
        wx.wxEVT_MIDDLE_UP: 'MIDDLE_UP',
        wx.wxEVT_MIDDLE_DCLICK: 'MIDDLE_DCLICK',
        wx.wxEVT_RIGHT_DOWN: 'RIGHT_DOWN',
        wx.wxEVT_RIGHT_UP: 'RIGHT_UP',
        wx.wxEVT_RIGHT_DCLICK: 'RIGHT_DCLICK',
        wx.wxEVT_MOTION: 'MOTION',
        wx.wxEVT_MOUSEWHEEL: 'MOUSEWHEEL',
        }

class DashboardPrefs(Preferences):

    showSections = schema.One(schema.Boolean, defaultValue = True)
    
class DashboardBlock(Table):
    """
    A block class for the Chandler Dashboard.

    This class works with the expectation that the delegate is the
    SectionedGridDelegate from the Sections module.
    """

    # A few extra character styles
    sectionLabelCharacterStyle = schema.One(Styles.CharacterStyle)
    sectionCountCharacterStyle = schema.One(Styles.CharacterStyle)
    
    schema.addClouds(
        copying = schema.Cloud(
            byRef = [sectionLabelCharacterStyle, sectionCountCharacterStyle]
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
        # Hack for Philippe, disabled until I can talk w/Jeffrey about it...
        autoTriageToo = wx.GetMouseState().AltDown()
        if autoTriageToo and wx.MessageBox(
            _(u"Are you sure you want to reset the triage status of everything in this collection?"),
            _(u"Automatic triage"), wx.OK | wx.CANCEL | wx.ICON_HAND) != wx.OK:
            return
        
        #import hotshot
        #print 'triaging'
        #prof = hotshot.Profile('triage.log')
        #prof.runcall(self._onTriageEvent, event, autoTriageToo)
        #prof.close()
        #print 'done triaging'
    
    #def _onTriageEvent(self, event, autoTriageToo):        
        # Don't fire all the observers (until we're done, that is).
        recurringEventsToHandle = set()
        attrsToFind = ((pim.EventStamp.modificationFor.name, None),
                       ('_sectionTriageStatus', None))
        with self.itsView.observersDeferred():
            with self.itsView.reindexingDeferred():
                for key in self.contents.iterkeys():
                    master, sectionTS = self.itsView.findValues(key, *attrsToFind)
                    if autoTriageToo or sectionTS is not None:
                        item = self.itsView[key]
                        item.purgeSectionTriageStatus()
                        if autoTriageToo:
                            if item.hasLocalAttributeValue('doAutoTriageOnDateChange'):
                                del item.doAutoTriageOnDateChange
                        
                            if master is None:
                                item.setTriageStatus('auto')
                            
                    if master is not None:
                        recurringEventsToHandle.add(master)
         
        # (We do this outside the deferrals because this depends on the indexes...
        for master in recurringEventsToHandle:
            if isinstance(master, UUID):
                master = self.itsView[master]
            pim.EventStamp(master).updateTriageStatus(checkOccurrences=autoTriageToo)
