#   Copyright (c) 2008 Open Source Applications Foundation
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

import wx, osaf, application
def run():
    """
        Regression test for Bug 11887 (Exception changing visible hours in multiweek (month) view)
        
        Left Mouse Down in SidebarGridWindow (0)
        Choose toolbar button 'Calendar' (4)
        Left Mouse Down in genstattext (6)
        Choose menu 'View > Visible Hours > 12 hours' (9)
    """

    wx.GetApp().RunRecordedScript ([
        (0, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'SidebarGridWindow'}, {'m_leftDown':True, 'm_x':72, 'm_y':110}),
        (1, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'SidebarGridWindow'}, {}),
        (2, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'SidebarGridWindow'}, {'m_x':72, 'm_y':99}),
        (3, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (4, wx.CommandEvent, {'associatedBlock':'ApplicationBarEventButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (5, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'TimedEventsFocusWindow'}, {}),
        (6, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'genstattext'}, {'m_leftDown':True, 'm_x':52, 'm_y':11}),
        (7, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'MultiWeekCanvasFocusWindow'}, {}),
        (8, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'genstattext'}, {'m_x':52, 'm_y':11}),
        (9, wx.CommandEvent, {'associatedBlock':'VisibleHour12Item', 'eventType':wx.EVT_MENU, 'sentTo':'__block__VisibleHoursMenu'}, {}),
    ])
    
    # Without the following, the framework seems happy to pass the
    # test even though event 5 unexpectedly raised an AttributeError.
    # So, let's check that the calendar preferences really were changed
    calendarPrefs = application.schema.ns('osaf.framework.blocks.calendar',
                               wx.GetApp().UIRepositoryView).calendarPrefs
    visibleHours = calendarPrefs.visibleHours
    if visibleHours != 12:
        raise AssertionError, "VisibleHours set to %s, should be 12" % (visibleHours,)
