import wx, osaf, application
def run():
    """
        Regression test for Bug 11887 (Exception changing visible hours in multiweek (month) view)
        
        Choose toolbar button 'Calendar' (0)
        Left Mouse Down in genstattext (2)
        Choose menu 'View > Visible Hours > 12 hours' (5)
    """

    wx.GetApp().RunRecordedScript ([
        (0, wx.CommandEvent, {'associatedBlock':'ApplicationBarEventButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (1, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'TimedEventsFocusWindow'}, {}),
        (2, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'genstattext'}, {'m_leftDown':True, 'm_x':52, 'm_y':11}),
        (3, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'MultiWeekCanvasFocusWindow'}, {}),
        (4, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'genstattext'}, {'m_x':52, 'm_y':11}),
        (5, wx.CommandEvent, {'associatedBlock':'VisibleHour12Item', 'eventType':wx.EVT_MENU, 'sentTo':'__block__VisibleHoursMenu'}, {}),
    ])
    
    # Without the following, the framework seems happy to pass the
    # test even though event 5 unexpectedly raised an AttributeError.
    # So, let's check that the calendar preferences really were changed
    calendarPrefs = application.schema.ns('osaf.framework.blocks.calendar',
                               wx.GetApp().UIRepositoryView).calendarPrefs
    visibleHours = calendarPrefs.visibleHours
    if visibleHours != 12:
        raise AssertionError, "VisibleHours set to %s, should be 12" % (visibleHours,)
