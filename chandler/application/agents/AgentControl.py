__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from wxPython.wx import *
import os

__all__ = ['wxAgentControl']

class wxAgentControl(wxPyControl):
    """ The widget associated with agents """

    def __getAgentItem(self):
        return Globals.repository[self.agentID]

    agent = property(__getAgentItem)

    def __init__(self, agentID):
        wxPyControl.__init__(self, self._GetToolBar(),
                             -1, wxDefaultPosition, wxSize(32,32),
                             wxNO_BORDER, wxDefaultValidator, 'wxAgentControl')

        self.agentID = agentID
        self.image = AgentImage()
        self.status = "idle"

        self.SetToolTipString(self.agent.GetName())

        EVT_PAINT(self, self._OnPaint)
        EVT_MOUSE_EVENTS(self, self._OnMouseEvent)

        # start a timer to redraw us every so often
        #self.timer = wxTimer(self, 1)
        #EVT_TIMER(self, 1, self._OnTimer)
        #self.timer.Start(1000)

    def AddToToolBar(self):
        toolbar = self._GetToolBar()
        toolbar.AddControl(self)
        toolbar.Realize()

    def _OnTimer(self, event):
        # This should really only happen when the agent sends us a notification
        newStatus = self._GetStatus()
        if newStatus != self.status:
            self.status = newStatus
            self.Refresh()

    def _OnPaint(self, event):
        # XXX This should paint an image based on the current status
        # of the agent
        (width, height) = self.GetClientSizeTuple()
        dc = wxPaintDC(self)
        dc.BeginDrawing()
        dc.Clear()
        self.image.Draw(dc, self.status)
        dc.EndDrawing()

    def _OnMouseEvent (self, event):
        if event.ButtonUp():
            print "buttonup"
            # XXX add code to pop up a dialog to manage the agent
            self.agent.DumpStatus()
            event.Skip()
            return True
        return False

    def _GetToolBar(self):
        return Globals.application.wxMainFrame.navigationBar

    def _GetStatus(self):
        status = self.agent.GetStatus('busyness')
        # anything over 0.5 is probably bad
        if status > 0.25:
            return 'sprinting'
        if status > 0.1:
            return 'running'

        return 'idle'

class AgentImageLoader:
    def __init__(self):
        self.imageCache = {}

    def LoadImage(self, path):
        if self.imageCache.has_key(path):
            return self.imageCache[path]
        self.imageCache[path] = wxImage(path)
        return self.imageCache[path]

_imageLoader = AgentImageLoader()

class AgentImage:
    def __init__(self):
        basepath = os.path.join("application", "agents", "images")
        self.images = { }
        files = os.listdir(basepath)
        for i in files:
            file = os.path.join(basepath, i)
            name = i.split('.')[0]
            self.images[name] = _imageLoader.LoadImage(file)

    def Draw(self, dc, status):

        shapes = ['headshape', 'hat', 'eyes']
        for i in shapes:
            bitmap = wxBitmapFromImage(self.images[i])
            dc.DrawBitmap(bitmap, 0, 0, True)

#        bitmap = wxBitmapFromImage(self.images[status])
#        dc.DrawBitmap(bitmap, 0, 0, True)


