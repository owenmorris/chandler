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


import wx

"""
Emulating User-level Actions
"""

def emulate_menu_accelerator(stringOrKeyCode, ctrlFlag=True, altFlag=False, shiftFlag=False):
    """
    Emulate typing a key accelerator that's handled by a menu.
    This searches through the items in the main frame's menu bar,
    and tries to find once whose accelerator matches.
    
    Unfortunately, just processing a keydown/keyup pair doesn't work,
    because this doesn't create native OS events, and its the native
    controls that do the accelerator -> menu item lookup.
    
    @param stringOrKeyCode: The keypress to emulate. Either specify one of the
      constants wx.WXK_* or a single-character str
    @type stringOrKeyCode: C{int} or C{str}.
    
    @param ctrlFlag: C{True} if you want to simulate the Control key
      being held down during the keypress. (This is the same as holding
      down the "open apple" key on the Mac).
    @type ctrlFlag: C{bool}
    
    @param altFlag: C{True} if you want to simulate the Alt key
      being held down during the keypress.
    @type altFlag: C{bool}
    
    @param shiftFlag: C{True} if you want to simulate the Shift key
      being held down during the keypress. If you pass in an upper-case
      C{stringOrKeyCode}, this will be set to C{True} automatically.
    @type shiftFlag: C{bool}
    
    @return: C{True} if a matching item is found, and it was dispatched
    successfully, and C{False} otherwise.
    @rtype: C{bool}
    """

    try:
        menuBar = wx.GetApp().mainFrame.GetMenuBar()
    except AttributeError:
        pass
    else:
    
        try:
            # We/wx seem to store all the keycodes in upper-case
            desiredKeyCode = ord(stringOrKeyCode.upper())
        except AttributeError:
            # not a str, assume int
            desiredKeyCode = stringOrKeyCode
        else:
            # it was a str
            assert len(stringOrKeyCode) == 1, "Pass in a single-character string to emulate_menu_accelerator"
            if stringOrKeyCode.isupper():
                shiftFlag = True
            
        # Figure out which wx.Accelerator we're trying to match
        desiredFlags = 0
        if ctrlFlag: desiredFlags |= wx.ACCEL_CTRL
        if altFlag: desiredFlags |= wx.ACCEL_ALT
        if shiftFlag: desiredFlags |= wx.ACCEL_SHIFT
        
        # Start off with the menus in the top-level menu bar
        menus = list(menuBar.GetMenu(i) for i in xrange(menuBar.GetMenuCount()))

        while menus:
            
            thisMenu = menus.pop(0)
            
            for item in thisMenu.GetMenuItems():
                accel = item.GetAccel()
                
                if (accel is not None and
                    desiredKeyCode == accel.GetKeyCode() and
                    desiredFlags == accel.GetFlags()):
                    
                    # OK, we found a match. Create an event ...
                    event = wx.CommandEvent(commandType=wx.EVT_MENU.evtType[0],
                                            winid=item.GetId())
                                           
                    # ... and dispatch it
                    return wx.GetApp().ProcessEvent(event)
                    
                if item.IsSubMenu():
                    menus.append(item.GetSubMenu())
            
    return False
    
def emulate_typing(string, ctrlFlag = False, altFlag = False, shiftFlag = False):
    """ emulate_typing the string into the current focused widget """
    
    success = True
    def set_event_info(event):
        # setup event info for a keypress event
        event.m_keyCode = keyCode
        event.m_rawCode = keyCode
        event.m_shiftDown = char.isupper() or shiftFlag
        event.m_controlDown = event.m_metaDown = ctrlFlag
        event.m_altDown = altFlag
        event.SetEventObject(widget)
    # for each key, check for specials, then try several approaches
    for char in string:
        keyCode = ord(char)
        if keyCode == wx.WXK_RETURN:
            emulate_return()
        elif keyCode == wx.WXK_TAB:
            emulate_tab(shiftFlag=shiftFlag)
        else:
            # in case the focus has changed, get the new focused widget
            widget = wx.Window_FindFocus()
            if widget is None:
                success = False
            else:
                # try calling any bound key handler
                keyPress = wx.KeyEvent(wx.wxEVT_KEY_DOWN)
                set_event_info(keyPress)
                downWorked = widget.ProcessEvent(keyPress)
                keyUp = wx.KeyEvent(wx.wxEVT_KEY_UP)
                set_event_info(keyUp)
                upWorked = widget.ProcessEvent(keyUp)
                if not (downWorked or upWorked): # key handler worked?
                    # try calling EmulateKeyPress

                    emulateMethod = getattr(widget, 'EmulateKeyPress',
                                            lambda k: False)

                    if (wx.Platform == "__WXMSW__" or
                        not emulateMethod(keyPress)): # emulate worked?
                        # try calling WriteText
                        writeMethod = getattr(widget, 'WriteText', None)
                        if writeMethod:
                            writeMethod(char)
                        else:
                            success = False # remember we had a failure
                if success:
                    wx.GetApp().Yield(True)
    return success

def emulate_tab(shiftFlag=False):
    if shiftFlag:
        flags = wx.NavigationKeyEvent.IsBackward
    else:
        flags = wx.NavigationKeyEvent.IsForward
    wx.Window_FindFocus().Navigate(flags)

def emulate_click(block, x=None, y=None, double=False, **kwds):
    """
    Simulates left mouse click on the given block or widget.
    
    You can pass in special keyword parameters like control=True to
    emulate that certain buttons are down. Supported values are
    control, shift, meta, and alt
    """
    try:
        widget =  block.widget
    except AttributeError:
        widget = block
    # grids have an inner window that recieves the events. Note that
    # this does NOT allow you to click on the column header. For that
    # use widget.GetGridColLabelWindow()
    if isinstance(widget, wx.grid.Grid):
        widget = widget.GetGridWindow()
        
    # Checkboxes don't seem to toggle based on manufactured mouse clicks,
    # (bug 3336) so we fake it.
    if isinstance(widget, wx.Button):
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED)
        clickEvent.SetEventObject(widget)
        widget.ProcessEvent(clickEvent)
    elif isinstance(widget, wx.CheckBox):
        widget.SetValue(not widget.GetValue())
        clickEvent = wx.CommandEvent(wx.wxEVT_COMMAND_CHECKBOX_CLICKED)
        clickEvent.SetEventObject(widget)
        widget.ProcessEvent(clickEvent)
    else: # do it the normal way   
        # event settings
        mouseEnter = wx.MouseEvent(wx.wxEVT_ENTER_WINDOW)
        if double:
            mouseDown = wx.MouseEvent(wx.wxEVT_LEFT_DCLICK)
        else:
            mouseDown = wx.MouseEvent(wx.wxEVT_LEFT_DOWN)
        mouseUp = wx.MouseEvent(wx.wxEVT_LEFT_UP)
        mouseLeave = wx.MouseEvent(wx.wxEVT_LEAVE_WINDOW)
        if x:
            mouseEnter.m_x = mouseDown.m_x = mouseUp.m_x = x
        if y:
            mouseEnter.m_y = mouseDown.m_y = mouseUp.m_y = y
    
        for event in (mouseEnter, mouseDown, mouseUp, mouseLeave):
            event.SetEventObject(widget)
            for keyDown in 'control', 'alt', 'shift', 'meta':
                if kwds.get(keyDown):
                    setattr(event, 'm_' + keyDown + 'Down', kwds.get(keyDown))
    
        # events processing
        widget.ProcessEvent(mouseEnter)
        widget.ProcessEvent(mouseDown)
        if not double:
            widget.ProcessEvent(mouseUp)
        widget.ProcessEvent(mouseLeave)
    # Give Yield to the App
    wx.GetApp().Yield(True)

def emulate_return(block=None):
    """ Simulates a return-key event in the given block """
    try:
        if block :
            widget = block.widget
        else :
            widget = wx.Window_FindFocus()
    except AttributeError:
        return False
    else:
        # return-key down
        ret_d = wx.KeyEvent(wx.wxEVT_KEY_DOWN)
        ret_d.m_keyCode = wx.WXK_RETURN
        ret_d.SetEventObject(widget)
        # return-key up
        ret_up = wx.KeyEvent(wx.wxEVT_KEY_UP)
        ret_up.m_keyCode = wx.WXK_RETURN
        ret_up.SetEventObject(widget)
        # text updated event
        tu = wx.CommandEvent(wx.wxEVT_COMMAND_TEXT_UPDATED)
        tu.SetEventObject(widget)
        # kill focus event
        kf = wx.FocusEvent(wx.wxEVT_KILL_FOCUS)
        kf.SetEventObject(widget)
        # Text enter
        ent = wx.CommandEvent(wx.wxEVT_COMMAND_TEXT_ENTER)
        ent.SetEventObject(widget)

        #work around for mac bug
        if widget is not None:
            widget.ProcessEvent(tu) #for start/end time and location field
        #work around for canvasItem
        if widget is not None:
            widget.ProcessEvent(kf) #for canvasItem title
            # events processing
        
            widget.ProcessEvent(ret_d)
            widget.ProcessEvent(ret_up)
        # Give Yield & Idle to the App
        idle()
        return True

def emulate_sidebarClick(sidebar, cellName, double=False, overlay=False):
    ''' Process a left click on the given cell in the given sidebar
        if overlay is true the overlay disk next to the collection name is checked
        otherwise the collection is selected'''
    #determine x coordinate offset based on overlay value
    xOffset = 24
    if overlay:
        xOffset=3 

    cellRect = None
    for i, item in enumerate(sidebar.contents):
        if item.displayName == cellName or item is cellName:
            #make sure its visible (not scrolled off screen)
            row = sidebar.widget.IndexToRow(i)
            sidebar.widget.MakeCellVisible(row, 0)
            cellRect = sidebar.widget.CalculateCellRect(row)
            break
    if cellRect:
        # events processing
        gw = sidebar.widget.GetGridWindow()
        # +3 work around for the sidebar bug
        emulate_click(gw, x=cellRect.GetX()+xOffset, y=cellRect.GetY()+3, double=double)
        return True
    else:
        return False

def idle():
    theApp = wx.GetApp()
    theApp.Yield(True)
    theApp.ProcessIdle()
    theApp.Yield(True)
