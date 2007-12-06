import wx, osaf, application
def run():
    """
        Choose menu 'Collection > New' (0)
        Type u'New' (4)
        Left Mouse Down in ApplicationBar (16)
        Choose toolbar button 'New' (18)
        Left Mouse Down in TriageStamp (20)
        Left Mouse Down in TriageStamp (24)
        Left Mouse Down in DashboardSummaryViewGridWindow (27)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Type u'Done' (35)
        Left Mouse Down in ApplicationBar (50)
        Choose toolbar button 'New' (52)
        Left Mouse Down in TriageStamp (54)
        Left Mouse Down in DashboardSummaryViewGridWindow (58)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Type u'Later' (66)
        Left Mouse Down in ApplicationBar (84)
        Choose toolbar button 'New' (86)
        Left Mouse Down in DashboardSummaryViewGridWindow (88)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Type u'Now' (96)
        Left Mouse Down in ApplicationBar (108)
        Choose toolbar button 'Triage' (110)
        Left Mouse Down in DashboardSummaryViewColLabelWindow (111)
        Left Mouse Down in DashboardSummaryViewGridWindow (113)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Left Mouse Down in DashboardSummaryViewAttributeEditor (118)
        Type u'v' (121)
        Left Mouse Down in DashboardSummaryViewGridWindow (126)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Left Mouse Down in DashboardSummaryViewAttributeEditor (131)
        Type u'v' (134)
        Left Mouse Down in DashboardSummaryViewGridWindow (139)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Left Mouse Down in DashboardSummaryViewAttributeEditor (144)
        Type u'v' (147)
        Left Mouse Down in DashboardSummaryViewGridWindow (152)
        Left Mouse Down in DashboardSummaryViewGridWindow (154)
        Left Mouse Down in DashboardSummaryViewGridWindow (156)
    """

    wx.GetApp().RunRecordedScript ([
        (0, wx.CommandEvent, {'associatedBlock':'NewCollectionItem', 'eventType':wx.EVT_MENU, 'sentTo':u'MainViewRoot'}, {}),
        (1, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'SidebarAttributeEditor'}, {}),
        (2, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':129, 'm_y':-193, 'UnicodeKey':16}),
        (3, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':129, 'm_y':-193, 'UnicodeKey':78}),
        (4, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':129, 'm_y':-193, 'UnicodeKey':78}),
        (5, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':129, 'm_y':-193, 'UnicodeKey':78}),
        (6, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':129, 'm_y':-193, 'UnicodeKey':16}),
        (7, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'N'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':129, 'm_y':-193, 'UnicodeKey':69}),
        (8, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'N'}, {'m_rawCode':101, 'm_keyCode':101, 'm_x':129, 'm_y':-193, 'UnicodeKey':101}),
        (9, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Ne'}, {'m_rawCode':87, 'm_keyCode':87, 'm_x':129, 'm_y':-193, 'UnicodeKey':87}),
        (10, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Ne'}, {'m_rawCode':119, 'm_keyCode':119, 'm_x':129, 'm_y':-193, 'UnicodeKey':119}),
        (11, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':129, 'm_y':-193, 'UnicodeKey':69}),
        (12, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':87, 'm_keyCode':87, 'm_x':129, 'm_y':-193, 'UnicodeKey':87}),
        (13, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'New'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':129, 'm_y':-193, 'UnicodeKey':13}),
        (14, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'SidebarGridWindow'}, {}),
        (15, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':151, 'm_y':-61, 'UnicodeKey':13}),
        (16, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'SidebarGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':286, 'm_y':26}),
        (17, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':286, 'm_y':26}),
        (18, wx.CommandEvent, {'associatedBlock':'ApplicationBarNewButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (19, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (20, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'TriageStamp', 'recordedFocusWindow':u'HeadlineBlockAEEditControl', 'recordedFocusWindowClass':osaf.framework.attributeEditors.DragAndDropTextCtrl.DragAndDropTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':34, 'm_y':20}),
        (21, wx.FocusEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'TriageStamp'}, {}),
        (22, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'TriageStamp'}, {'m_x':34, 'm_y':20}),
        (23, wx.PyCommandEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_BUTTON, 'sentTo':u'TriageStamp', 'recordedFocusWindow':u'TriageStamp', 'recordedFocusWindowClass':osaf.framework.blocks.ControlBlocks.wxChandlerMultiStateButton}, {}),
        (24, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'TriageStamp'}, {'m_leftDown':True, 'm_x':34, 'm_y':20}),
        (25, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'TriageStamp'}, {'m_x':34, 'm_y':20}),
        (26, wx.PyCommandEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_BUTTON, 'sentTo':u'TriageStamp'}, {}),
        (27, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':198, 'm_y':28}),
        (28, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (29, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':198, 'm_y':28}),
        (30, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':198, 'm_y':28}),
        (31, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (32, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,8)}, {'m_x':42, 'm_y':8}),
        (33, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':44, 'm_y':10, 'UnicodeKey':16}),
        (34, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':68, 'm_keyCode':68, 'm_shiftDown':True, 'm_x':44, 'm_y':10, 'UnicodeKey':68}),
        (35, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_rawCode':68, 'm_keyCode':68, 'm_shiftDown':True, 'm_x':44, 'm_y':10, 'UnicodeKey':68}),
        (36, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':44, 'm_y':10, 'UnicodeKey':16}),
        (37, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':68, 'm_keyCode':68, 'm_x':44, 'm_y':10, 'UnicodeKey':68}),
        (38, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'D'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':44, 'm_y':10, 'UnicodeKey':79}),
        (39, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'D'}, {'m_rawCode':111, 'm_keyCode':111, 'm_x':44, 'm_y':10, 'UnicodeKey':111}),
        (40, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Do'}, {'m_rawCode':78, 'm_keyCode':78, 'm_x':44, 'm_y':10, 'UnicodeKey':78}),
        (41, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Do'}, {'m_rawCode':110, 'm_keyCode':110, 'm_x':44, 'm_y':10, 'UnicodeKey':110}),
        (42, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':44, 'm_y':10, 'UnicodeKey':79}),
        (43, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Don'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':44, 'm_y':10, 'UnicodeKey':69}),
        (44, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Don'}, {'m_rawCode':101, 'm_keyCode':101, 'm_x':44, 'm_y':10, 'UnicodeKey':101}),
        (45, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':78, 'm_keyCode':78, 'm_x':44, 'm_y':10, 'UnicodeKey':78}),
        (46, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':44, 'm_y':10, 'UnicodeKey':69}),
        (47, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Done'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':44, 'm_y':10, 'UnicodeKey':13}),
        (48, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (49, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':198, 'm_y':28, 'UnicodeKey':13}),
        (50, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':289, 'm_y':35}),
        (51, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':289, 'm_y':35}),
        (52, wx.CommandEvent, {'associatedBlock':'ApplicationBarNewButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (53, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (54, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'TriageStamp', 'recordedFocusWindow':u'HeadlineBlockAEEditControl', 'recordedFocusWindowClass':osaf.framework.attributeEditors.DragAndDropTextCtrl.DragAndDropTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':13, 'm_y':16}),
        (55, wx.FocusEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'TriageStamp'}, {}),
        (56, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'TriageStamp'}, {'m_x':13, 'm_y':16}),
        (57, wx.PyCommandEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_BUTTON, 'sentTo':u'TriageStamp', 'recordedFocusWindow':u'TriageStamp', 'recordedFocusWindowClass':osaf.framework.blocks.ControlBlocks.wxChandlerMultiStateButton}, {}),
        (58, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':196, 'm_y':31}),
        (59, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (60, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':196, 'm_y':31}),
        (61, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':196, 'm_y':31}),
        (62, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (63, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,8)}, {'m_x':40, 'm_y':11}),
        (64, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':42, 'm_y':13, 'UnicodeKey':16}),
        (65, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':76, 'm_keyCode':76, 'm_shiftDown':True, 'm_x':42, 'm_y':13, 'UnicodeKey':76}),
        (66, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_rawCode':76, 'm_keyCode':76, 'm_shiftDown':True, 'm_x':42, 'm_y':13, 'UnicodeKey':76}),
        (67, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':76, 'm_keyCode':76, 'm_shiftDown':True, 'm_x':42, 'm_y':13, 'UnicodeKey':76}),
        (68, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':42, 'm_y':13, 'UnicodeKey':16}),
        (69, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'L'}, {'m_rawCode':65, 'm_keyCode':65, 'm_x':42, 'm_y':13, 'UnicodeKey':65}),
        (70, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'L'}, {'m_rawCode':97, 'm_keyCode':97, 'm_x':42, 'm_y':13, 'UnicodeKey':97}),
        (71, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'La'}, {'m_rawCode':84, 'm_keyCode':84, 'm_x':42, 'm_y':13, 'UnicodeKey':84}),
        (72, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'La'}, {'m_rawCode':116, 'm_keyCode':116, 'm_x':42, 'm_y':13, 'UnicodeKey':116}),
        (73, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':65, 'm_keyCode':65, 'm_x':42, 'm_y':13, 'UnicodeKey':65}),
        (74, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':84, 'm_keyCode':84, 'm_x':42, 'm_y':13, 'UnicodeKey':84}),
        (75, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Lat'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':42, 'm_y':13, 'UnicodeKey':69}),
        (76, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Lat'}, {'m_rawCode':101, 'm_keyCode':101, 'm_x':42, 'm_y':13, 'UnicodeKey':101}),
        (77, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Late'}, {'m_rawCode':82, 'm_keyCode':82, 'm_x':42, 'm_y':13, 'UnicodeKey':82}),
        (78, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Late'}, {'m_rawCode':114, 'm_keyCode':114, 'm_x':42, 'm_y':13, 'UnicodeKey':114}),
        (79, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':42, 'm_y':13, 'UnicodeKey':69}),
        (80, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':82, 'm_keyCode':82, 'm_x':42, 'm_y':13, 'UnicodeKey':82}),
        (81, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Later'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':42, 'm_y':13, 'UnicodeKey':13}),
        (82, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (83, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':196, 'm_y':31, 'UnicodeKey':13}),
        (84, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':285, 'm_y':27}),
        (85, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':285, 'm_y':27}),
        (86, wx.CommandEvent, {'associatedBlock':'ApplicationBarNewButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (87, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (88, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'HeadlineBlockAEEditControl', 'recordedFocusWindowClass':osaf.framework.attributeEditors.DragAndDropTextCtrl.DragAndDropTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':188, 'm_y':33}),
        (89, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (90, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':188, 'm_y':33}),
        (91, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':188, 'm_y':33}),
        (92, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (93, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,8)}, {'m_x':32, 'm_y':13}),
        (94, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':34, 'm_y':15, 'UnicodeKey':16}),
        (95, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':34, 'm_y':15, 'UnicodeKey':78}),
        (96, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':34, 'm_y':15, 'UnicodeKey':78}),
        (97, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':34, 'm_y':15, 'UnicodeKey':78}),
        (98, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':34, 'm_y':15, 'UnicodeKey':16}),
        (99, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'N'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':34, 'm_y':15, 'UnicodeKey':79}),
        (100, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'N'}, {'m_rawCode':111, 'm_keyCode':111, 'm_x':34, 'm_y':15, 'UnicodeKey':111}),
        (101, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':34, 'm_y':15, 'UnicodeKey':79}),
        (102, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'No'}, {'m_rawCode':87, 'm_keyCode':87, 'm_x':34, 'm_y':15, 'UnicodeKey':87}),
        (103, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'No'}, {'m_rawCode':119, 'm_keyCode':119, 'm_x':34, 'm_y':15, 'UnicodeKey':119}),
        (104, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':87, 'm_keyCode':87, 'm_x':34, 'm_y':15, 'UnicodeKey':87}),
        (105, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Now'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':34, 'm_y':15, 'UnicodeKey':13}),
        (106, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (107, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':188, 'm_y':33, 'UnicodeKey':13}),
        (108, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':550, 'm_y':17}),
        (109, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':550, 'm_y':17}),
        (110, wx.CommandEvent, {'associatedBlock':'TriageButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (111, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewColLabelWindow'}, {'m_leftDown':True, 'm_x':499, 'm_y':9}),
        (112, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewColLabelWindow'}, {'m_x':499, 'm_y':9}),
        (113, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':170, 'm_y':30}),
        (114, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':170, 'm_y':30}),
        (115, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':170, 'm_y':30}),
        (116, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (117, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,4)}, {'m_x':14, 'm_y':10}),
        (118, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Done'}, {'m_leftDown':True, 'm_x':66, 'm_y':5}),
        (119, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (4,4)}, {'m_x':66, 'm_y':5}),
        (120, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Done'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':68, 'm_y':7, 'UnicodeKey':86}),
        (121, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Done'}, {'m_rawCode':118, 'm_keyCode':118, 'm_x':68, 'm_y':7, 'UnicodeKey':118}),
        (122, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':68, 'm_y':7, 'UnicodeKey':86}),
        (123, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Donev'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':68, 'm_y':7, 'UnicodeKey':13}),
        (124, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (125, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':222, 'm_y':25, 'UnicodeKey':13}),
        (126, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':170, 'm_y':64}),
        (127, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':170, 'm_y':64}),
        (128, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':170, 'm_y':64}),
        (129, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (130, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,5)}, {'m_x':14, 'm_y':6}),
        (131, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Later'}, {'m_leftDown':True, 'm_x':55, 'm_y':5}),
        (132, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (5,5)}, {'m_x':55, 'm_y':5}),
        (133, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Later'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':57, 'm_y':7, 'UnicodeKey':86}),
        (134, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Later'}, {'m_rawCode':118, 'm_keyCode':118, 'm_x':57, 'm_y':7, 'UnicodeKey':118}),
        (135, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':57, 'm_y':7, 'UnicodeKey':86}),
        (136, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Laterv'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':57, 'm_y':7, 'UnicodeKey':13}),
        (137, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (138, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':211, 'm_y':63, 'UnicodeKey':13}),
        (139, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':180, 'm_y':104}),
        (140, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':180, 'm_y':104}),
        (141, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':180, 'm_y':104}),
        (142, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (143, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,3)}, {'m_x':24, 'm_y':8}),
        (144, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Now'}, {'m_leftDown':True, 'm_x':37, 'm_y':9}),
        (145, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (3,3)}, {'m_x':37, 'm_y':9}),
        (146, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Now'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':39, 'm_y':11, 'UnicodeKey':86}),
        (147, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Now'}, {'m_rawCode':118, 'm_keyCode':118, 'm_x':39, 'm_y':11, 'UnicodeKey':118}),
        (148, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':39, 'm_y':11, 'UnicodeKey':86}),
        (149, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Nowv'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':39, 'm_y':11, 'UnicodeKey':13}),
        (150, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (151, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':193, 'm_y':105, 'UnicodeKey':13}),
        (152, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':19, 'm_y':6}),
        (153, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':19, 'm_y':6}),
        (154, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':20, 'm_y':26}),
        (155, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':20, 'm_y':26}),
        (156, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':22, 'm_y':45}),
        (157, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':22, 'm_y':45}),
    ])
