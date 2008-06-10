import wx, osaf, application
def run():
    wx.GetApp().RunRecordedScript ([
        (0, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar'}, {'m_leftDown':True, 'm_x':117, 'm_y':24}),
        (1, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':117, 'm_y':24}),
        (2, wx.CommandEvent, {'associatedBlock':'ApplicationBarTaskButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (3, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar'}, {'m_leftDown':True, 'm_x':284, 'm_y':27}),
        (4, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':284, 'm_y':27}),
        (5, wx.CommandEvent, {'associatedBlock':'NewItemItem', 'eventType':wx.EVT_MENU, 'sentTo':'__block__NewItemMenu'}, {}),
        (6, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (7, wx.MouseEvent, {'associatedBlock':'NotesBlock', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'NotesBlock', 'recordedFocusWindow':u'HeadlineBlockAEEditControl', 'recordedFocusWindowClass':osaf.framework.attributeEditors.DragAndDropTextCtrl.DragAndDropTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':71, 'm_y':56}),
        (8, wx.FocusEvent, {'associatedBlock':'NotesBlock', 'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'NotesBlock'}, {}),
        (9, wx.MouseEvent, {'associatedBlock':'NotesBlock', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'NotesBlock', 'selectionRange': (0,0), 'lastWidgetValue':u''}, {'m_x':71, 'm_y':62}),
        (10, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'HeadlineBlockAEStaticControl', 'recordedFocusWindow':u'NotesBlock', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u''}, {'m_leftDown':True, 'm_x':29, 'm_y':12}),
        (11, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'HeadlineBlockAEStaticControl', 'lastWidgetValue':u'Untitled'}, {'m_x':29, 'm_y':12}),
        (12, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (13, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'HeadlineBlockAEEditControl', 'recordedFocusWindow':u'HeadlineBlockAEEditControl', 'recordedFocusWindowClass':osaf.framework.attributeEditors.DragAndDropTextCtrl.DragAndDropTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':27, 'm_y':10}),
        (14, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'HeadlineBlockAEEditControl', 'selectionRange': (3,3), 'lastWidgetValue':u'Untitled'}, {'m_x':27, 'm_y':10}),
    ])
