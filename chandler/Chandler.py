#!/bin/env python
#----------------------------------------------------------------------------
# Name:         Chandler.py
# Author:       Open Source Application Foundation
# Created:      XX/XX/XX
# Copyright:    
#----------------------------------------------------------------------------

from wxPython.wx import *
from wxPython.xrc import *

import cal.CalendarView

class MyFrame(wxFrame):
    def __init__(self, parent, id, title,
                 pos = wxPyDefaultPosition, size = wxPyDefaultSize,
                 style = wxDEFAULT_FRAME_STYLE ):
        wxFrame.__init__(self, parent, id, title, pos, size, style)

        resources = wxXmlResource ("resources/resources.xrc")
        self.SetMenuBar (resources.LoadMenuBar ("MenuBar"))
        self.SetToolBar (resources.LoadToolBar (self, "ToolBar"))

        self.CreateStatusBar(1)
        self.SetStatusText("Welcome!")
        
        # insert main window here
        view = cal.CalendarView.CalendarView(self)
        
        # WDR: handler declarations for MyFrame
        EVT_MENU(self, wxID_ABOUT, self.OnAbout)
        EVT_MENU(self, XRCID ("menu_quit"), self.OnQuit)
        EVT_CLOSE(self, self.OnCloseWindow)

    def OnAbout(self, event):
        dialog = wxMessageDialog(self, "Welcome to Chandler 0.01\n(C)opyright OSAF",
            "About Chandler", wxOK|wxICON_INFORMATION )
        dialog.CentreOnParent()
        dialog.ShowModal()
        dialog.Destroy()
    
    def OnQuit(self, event):
        self.Close(true)
    
    def OnCloseWindow(self, event):
        self.Destroy()
    

#----------------------------------------------------------------------------

class MyApp(wxApp):
    
    def OnInit(self):
        wxInitAllImageHandlers()
        frame = MyFrame(None, -1, "Chandler", wxPoint(20,20), wxSize(500,340) )
        frame.Show(true)
        
        return true

#----------------------------------------------------------------------------

app = MyApp(1)
app.MainLoop()

