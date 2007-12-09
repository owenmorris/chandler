import wx, osaf, application

_platform_exclusions_ = ("darwin")

def run():
    """
        Choose menu 'Collection > New' (0)
        Type u'Test' (4)
        Left Mouse Down in ApplicationBar (19)
        Choose toolbar button 'New' (21)
        Left Mouse Down in TriageStamp (23)
        Left Mouse Down in TriageStamp (26)
        Left Mouse Down in DashboardSummaryViewGridWindow (29)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Type u'Done' (37)
        Left Mouse Down in ApplicationBar (52)
        Choose toolbar button 'New' (54)
        Left Mouse Down in TriageStamp (56)
        Left Mouse Down in DashboardSummaryViewGridWindow (59)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Type u'Later' (67)
        Left Mouse Down in ApplicationBar (85)
        Choose toolbar button 'New' (87)
        Left Mouse Down in DashboardSummaryViewGridWindow (89)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Type u'Now' (97)
        Left Mouse Down in ApplicationBar (109)
        Choose toolbar button 'Triage' (111)
        Left Mouse Down in DashboardSummaryViewColLabelWindow (112)
        Left Mouse Down in DashboardSummaryViewGridWindow (114)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Left Mouse Down in DashboardSummaryViewAttributeEditor (119)
        Type u'v' (122)
        Left Mouse Down in DashboardSummaryViewGridWindow (127)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Left Mouse Down in DashboardSummaryViewAttributeEditor (132)
        Type u'v' (135)
        Left Mouse Down in DashboardSummaryViewGridWindow (140)
        Left Mouse Double Click in DashboardSummaryViewGridWindow
        Left Mouse Down in DashboardSummaryViewAttributeEditor (145)
        Type u'v' (148)
        Left Mouse Down in DashboardSummaryViewGridWindow (153)
        Left Mouse Down in DashboardSummaryViewGridWindow (155)
        Left Mouse Down in DashboardSummaryViewGridWindow (157)
    """

    wx.GetApp().RunRecordedScript ([
        (0, wx.CommandEvent, {'associatedBlock':'NewCollectionItem', 'eventType':wx.EVT_MENU, 'sentTo':u'MainViewRoot'}, {}),
        (1, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'SidebarAttributeEditor'}, {}),
        (2, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':126, 'm_y':-190, 'UnicodeKey':16}),
        (3, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':84, 'm_keyCode':84, 'm_shiftDown':True, 'm_x':126, 'm_y':-190, 'UnicodeKey':84}),
        (4, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':84, 'm_keyCode':84, 'm_shiftDown':True, 'm_x':126, 'm_y':-190, 'UnicodeKey':84}),
        (5, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':84, 'm_keyCode':84, 'm_shiftDown':True, 'm_x':126, 'm_y':-190, 'UnicodeKey':84}),
        (6, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':126, 'm_y':-190, 'UnicodeKey':16}),
        (7, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'T'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':126, 'm_y':-190, 'UnicodeKey':69}),
        (8, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'T'}, {'m_rawCode':101, 'm_keyCode':101, 'm_x':126, 'm_y':-190, 'UnicodeKey':101}),
        (9, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':126, 'm_y':-190, 'UnicodeKey':69}),
        (10, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Te'}, {'m_rawCode':83, 'm_keyCode':83, 'm_x':126, 'm_y':-190, 'UnicodeKey':83}),
        (11, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Te'}, {'m_rawCode':115, 'm_keyCode':115, 'm_x':126, 'm_y':-190, 'UnicodeKey':115}),
        (12, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Tes'}, {'m_rawCode':84, 'm_keyCode':84, 'm_x':126, 'm_y':-190, 'UnicodeKey':84}),
        (13, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Tes'}, {'m_rawCode':116, 'm_keyCode':116, 'm_x':126, 'm_y':-190, 'UnicodeKey':116}),
        (14, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':83, 'm_keyCode':83, 'm_x':126, 'm_y':-190, 'UnicodeKey':83}),
        (15, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarAttributeEditor'}, {'m_rawCode':84, 'm_keyCode':84, 'm_x':126, 'm_y':-190, 'UnicodeKey':84}),
        (16, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'SidebarAttributeEditor', 'lastWidgetValue':u'Test'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':126, 'm_y':-190, 'UnicodeKey':13}),
        (17, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'SidebarGridWindow'}, {}),
        (18, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'SidebarGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':148, 'm_y':-58, 'UnicodeKey':13}),
        (19, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'SidebarGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':280, 'm_y':22}),
        (20, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':280, 'm_y':22}),
        (21, wx.CommandEvent, {'associatedBlock':'ApplicationBarNewButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (22, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (23, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'TriageStamp', 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':15, 'm_y':18}),
        (24, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'TriageStamp'}, {'m_x':15, 'm_y':18}),
        (25, wx.PyCommandEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_BUTTON, 'sentTo':u'TriageStamp'}, {}),
        (26, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'TriageStamp'}, {'m_leftDown':True, 'm_x':15, 'm_y':18}),
        (27, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'TriageStamp'}, {'m_x':15, 'm_y':18}),
        (28, wx.PyCommandEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_BUTTON, 'sentTo':u'TriageStamp'}, {}),
        (29, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':184, 'm_y':29}),
        (30, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (31, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':184, 'm_y':29}),
        (32, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':184, 'm_y':29}),
        (33, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (34, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,8)}, {'m_x':28, 'm_y':9}),
        (35, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':30, 'm_y':11, 'UnicodeKey':16}),
        (36, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':68, 'm_keyCode':68, 'm_shiftDown':True, 'm_x':30, 'm_y':11, 'UnicodeKey':68}),
        (37, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_rawCode':68, 'm_keyCode':68, 'm_shiftDown':True, 'm_x':30, 'm_y':11, 'UnicodeKey':68}),
        (38, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':30, 'm_y':11, 'UnicodeKey':16}),
        (39, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':68, 'm_keyCode':68, 'm_x':30, 'm_y':11, 'UnicodeKey':68}),
        (40, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'D'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':30, 'm_y':11, 'UnicodeKey':79}),
        (41, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'D'}, {'m_rawCode':111, 'm_keyCode':111, 'm_x':30, 'm_y':11, 'UnicodeKey':111}),
        (42, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Do'}, {'m_rawCode':78, 'm_keyCode':78, 'm_x':30, 'm_y':11, 'UnicodeKey':78}),
        (43, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Do'}, {'m_rawCode':110, 'm_keyCode':110, 'm_x':30, 'm_y':11, 'UnicodeKey':110}),
        (44, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':30, 'm_y':11, 'UnicodeKey':79}),
        (45, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Don'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':30, 'm_y':11, 'UnicodeKey':69}),
        (46, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Don'}, {'m_rawCode':101, 'm_keyCode':101, 'm_x':30, 'm_y':11, 'UnicodeKey':101}),
        (47, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':78, 'm_keyCode':78, 'm_x':30, 'm_y':11, 'UnicodeKey':78}),
        (48, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':30, 'm_y':11, 'UnicodeKey':69}),
        (49, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Done'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':30, 'm_y':11, 'UnicodeKey':13}),
        (50, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (51, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':184, 'm_y':29, 'UnicodeKey':13}),
        (52, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':275, 'm_y':17}),
        (53, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':275, 'm_y':17}),
        (54, wx.CommandEvent, {'associatedBlock':'ApplicationBarNewButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (55, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (56, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'TriageStamp', 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':24, 'm_y':15}),
        (57, wx.MouseEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'TriageStamp'}, {'m_x':24, 'm_y':15}),
        (58, wx.PyCommandEvent, {'associatedBlock':'TriageStamp', 'eventType':wx.EVT_BUTTON, 'sentTo':u'TriageStamp'}, {}),
        (59, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':166, 'm_y':28}),
        (60, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (61, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':166, 'm_y':28}),
        (62, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':166, 'm_y':28}),
        (63, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (64, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,8)}, {'m_x':10, 'm_y':8}),
        (65, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':17, 'm_y':9, 'UnicodeKey':16}),
        (66, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':76, 'm_keyCode':76, 'm_shiftDown':True, 'm_x':17, 'm_y':9, 'UnicodeKey':76}),
        (67, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_rawCode':76, 'm_keyCode':76, 'm_shiftDown':True, 'm_x':17, 'm_y':9, 'UnicodeKey':76}),
        (68, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':76, 'm_keyCode':76, 'm_shiftDown':True, 'm_x':17, 'm_y':9, 'UnicodeKey':76}),
        (69, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':17, 'm_y':9, 'UnicodeKey':16}),
        (70, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'L'}, {'m_rawCode':65, 'm_keyCode':65, 'm_x':17, 'm_y':9, 'UnicodeKey':65}),
        (71, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'L'}, {'m_rawCode':97, 'm_keyCode':97, 'm_x':17, 'm_y':9, 'UnicodeKey':97}),
        (72, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'La'}, {'m_rawCode':84, 'm_keyCode':84, 'm_x':17, 'm_y':9, 'UnicodeKey':84}),
        (73, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'La'}, {'m_rawCode':116, 'm_keyCode':116, 'm_x':17, 'm_y':9, 'UnicodeKey':116}),
        (74, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':65, 'm_keyCode':65, 'm_x':17, 'm_y':9, 'UnicodeKey':65}),
        (75, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':84, 'm_keyCode':84, 'm_x':17, 'm_y':9, 'UnicodeKey':84}),
        (76, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Lat'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':17, 'm_y':9, 'UnicodeKey':69}),
        (77, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Lat'}, {'m_rawCode':101, 'm_keyCode':101, 'm_x':17, 'm_y':9, 'UnicodeKey':101}),
        (78, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Late'}, {'m_rawCode':82, 'm_keyCode':82, 'm_x':17, 'm_y':9, 'UnicodeKey':82}),
        (79, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Late'}, {'m_rawCode':114, 'm_keyCode':114, 'm_x':17, 'm_y':9, 'UnicodeKey':114}),
        (80, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':69, 'm_keyCode':69, 'm_x':17, 'm_y':9, 'UnicodeKey':69}),
        (81, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':82, 'm_keyCode':82, 'm_x':17, 'm_y':9, 'UnicodeKey':82}),
        (82, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Later'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':17, 'm_y':9, 'UnicodeKey':13}),
        (83, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (84, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':171, 'm_y':27, 'UnicodeKey':13}),
        (85, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':287, 'm_y':34}),
        (86, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':287, 'm_y':34}),
        (87, wx.CommandEvent, {'associatedBlock':'ApplicationBarNewButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (88, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'HeadlineBlockAEEditControl'}, {}),
        (89, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'HeadlineBlockAEEditControl', 'recordedFocusWindowClass':osaf.framework.attributeEditors.DragAndDropTextCtrl.DragAndDropTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_leftDown':True, 'm_x':182, 'm_y':31}),
        (90, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (91, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':182, 'm_y':31}),
        (92, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':182, 'm_y':31}),
        (93, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (94, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,8)}, {'m_x':26, 'm_y':11}),
        (95, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':16, 'm_keyCode':306, 'm_shiftDown':True, 'm_x':28, 'm_y':13, 'UnicodeKey':16}),
        (96, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Untitled'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':28, 'm_y':13, 'UnicodeKey':78}),
        (97, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Untitled'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':28, 'm_y':13, 'UnicodeKey':78}),
        (98, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':78, 'm_keyCode':78, 'm_shiftDown':True, 'm_x':28, 'm_y':13, 'UnicodeKey':78}),
        (99, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':16, 'm_keyCode':306, 'm_x':28, 'm_y':13, 'UnicodeKey':16}),
        (100, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'N'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':28, 'm_y':13, 'UnicodeKey':79}),
        (101, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'N'}, {'m_rawCode':111, 'm_keyCode':111, 'm_x':28, 'm_y':13, 'UnicodeKey':111}),
        (102, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'No'}, {'m_rawCode':87, 'm_keyCode':87, 'm_x':28, 'm_y':13, 'UnicodeKey':87}),
        (103, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'No'}, {'m_rawCode':119, 'm_keyCode':119, 'm_x':28, 'm_y':13, 'UnicodeKey':119}),
        (104, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':79, 'm_keyCode':79, 'm_x':28, 'm_y':13, 'UnicodeKey':79}),
        (105, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':87, 'm_keyCode':87, 'm_x':28, 'm_y':13, 'UnicodeKey':87}),
        (106, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Now'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':28, 'm_y':13, 'UnicodeKey':13}),
        (107, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (108, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':182, 'm_y':31, 'UnicodeKey':13}),
        (109, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'ApplicationBar', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':523, 'm_y':26}),
        (110, wx.MouseEvent, {'associatedBlock':'ApplicationBar', 'eventType':wx.EVT_LEFT_UP, 'sentTo':u'ApplicationBar'}, {'m_x':523, 'm_y':26}),
        (111, wx.CommandEvent, {'associatedBlock':'TriageButton', 'eventType':wx.EVT_MENU, 'sentTo':u'ApplicationBar'}, {}),
        (112, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewColLabelWindow'}, {'m_leftDown':True, 'm_x':500, 'm_y':11}),
        (113, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewColLabelWindow'}, {'m_x':500, 'm_y':11}),
        (114, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':177, 'm_y':28}),
        (115, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':177, 'm_y':29}),
        (116, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':177, 'm_y':29}),
        (117, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (118, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,4)}, {'m_x':21, 'm_y':9}),
        (119, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Done'}, {'m_leftDown':True, 'm_x':43, 'm_y':7}),
        (120, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (4,4)}, {'m_x':43, 'm_y':7}),
        (121, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Done'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':45, 'm_y':9, 'UnicodeKey':86}),
        (122, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Done'}, {'m_rawCode':118, 'm_keyCode':118, 'm_x':45, 'm_y':9, 'UnicodeKey':118}),
        (123, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':45, 'm_y':9, 'UnicodeKey':86}),
        (124, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Donev'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':45, 'm_y':9, 'UnicodeKey':13}),
        (125, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (126, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':199, 'm_y':27, 'UnicodeKey':13}),
        (127, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':181, 'm_y':69}),
        (128, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':181, 'm_y':69}),
        (129, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':181, 'm_y':69}),
        (130, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (131, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,5)}, {'m_x':25, 'm_y':11}),
        (132, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Later'}, {'m_leftDown':True, 'm_x':61, 'm_y':7}),
        (133, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (5,5)}, {'m_x':61, 'm_y':7}),
        (134, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Later'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':63, 'm_y':9, 'UnicodeKey':86}),
        (135, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Later'}, {'m_rawCode':118, 'm_keyCode':118, 'm_x':63, 'm_y':9, 'UnicodeKey':118}),
        (136, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':63, 'm_y':9, 'UnicodeKey':86}),
        (137, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Laterv'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':63, 'm_y':9, 'UnicodeKey':13}),
        (138, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (139, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':217, 'm_y':65, 'UnicodeKey':13}),
        (140, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':170, 'm_y':101}),
        (141, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':170, 'm_y':101}),
        (142, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DCLICK, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':170, 'm_y':101}),
        (143, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {}),
        (144, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (0,3)}, {'m_x':14, 'm_y':5}),
        (145, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindow':u'DashboardSummaryViewAttributeEditor', 'recordedFocusWindowClass':osaf.framework.attributeEditors.AETypeOverTextCtrl.AENonTypeOverTextCtrl, 'lastWidgetValue':u'Now'}, {'m_leftDown':True, 'm_x':38, 'm_y':7}),
        (146, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'selectionRange': (3,3)}, {'m_x':38, 'm_y':7}),
        (147, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Now'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':40, 'm_y':9, 'UnicodeKey':86}),
        (148, wx.KeyEvent, {'eventType':wx.EVT_CHAR, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Now'}, {'m_rawCode':118, 'm_keyCode':118, 'm_x':40, 'm_y':9, 'UnicodeKey':118}),
        (149, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewAttributeEditor'}, {'m_rawCode':86, 'm_keyCode':86, 'm_x':40, 'm_y':9, 'UnicodeKey':86}),
        (150, wx.KeyEvent, {'eventType':wx.EVT_KEY_DOWN, 'sentTo':u'DashboardSummaryViewAttributeEditor', 'lastWidgetValue':u'Nowv'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':40, 'm_y':9, 'UnicodeKey':13}),
        (151, wx.FocusEvent, {'eventType':wx.EVT_SET_FOCUS, 'sentTo':u'DashboardSummaryViewGridWindow'}, {}),
        (152, wx.KeyEvent, {'eventType':wx.EVT_KEY_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_rawCode':13, 'm_keyCode':13, 'm_x':194, 'm_y':103, 'UnicodeKey':13}),
        (153, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow', 'recordedFocusWindow':u'DashboardSummaryViewGridWindow', 'recordedFocusWindowClass':wx.Window}, {'m_leftDown':True, 'm_x':19, 'm_y':8}),
        (154, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':19, 'm_y':8}),
        (155, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':19, 'm_y':26}),
        (156, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':19, 'm_y':26}),
        (157, wx.MouseEvent, {'eventType':wx.EVT_LEFT_DOWN, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_leftDown':True, 'm_x':19, 'm_y':46}),
        (158, wx.MouseEvent, {'eventType':wx.EVT_LEFT_UP, 'sentTo':u'DashboardSummaryViewGridWindow'}, {'m_x':19, 'm_y':46}),
    ])
