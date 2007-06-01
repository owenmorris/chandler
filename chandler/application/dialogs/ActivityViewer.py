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
from i18n import ChandlerMessageFactory as _
from osaf.activity import *


# TODO: kill the window when Chandler exits
# TODO: render failures
# TODO: add cancel buttons
# TODO: upon completion, possibly render "success" for a few seconds


def Show():
    win = ActivityViewerFrame(None, -1, _(u"Activity Viewer"),
        size=(450,200), style=wx.DEFAULT_FRAME_STYLE)
    win.Show()



class ActivityViewerFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        super(ActivityViewerFrame, self).__init__(*args, **kwds)
        self.listener = Listener(callback=self.callback)
        self.widgets = { }

        self.panel = wx.Panel(self, -1)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnCloseWindow(self, event):
        self.listener.unregister()
        self.Destroy()

    def callback(self, activity, *args, **kwds):
        # Can be called from any thread; will call _callback in main thread
        wx.GetApp().PostAsyncEvent(self._callback, activity, *args, **kwds)

    def _callback(self, activity, *args, **kwds):
        # Must be called in main thread

        if 'status' in kwds:
            status = kwds['status']
            if status in (STATUS_ABORTED, STATUS_FAILED, STATUS_COMPLETE):
                self.removeWidget(activity)
                return

        self.updateWidget(activity, *args, **kwds)

    def updateWidget(self, activity, *args, **kwds):
        if activity.id in self.widgets:
            widget = self.widgets[activity.id]
        else:
            widget = ActivityWidget(self.panel, self.sizer, activity)
            self.widgets[activity.id] = widget
        widget.update(*args, **kwds)
        self._fix()

    def removeWidget(self, activity):
        if activity.id in self.widgets:
            widget = self.widgets[activity.id]
            widget.destroy(self.sizer)
            del self.widgets[activity.id]
            self._fix()

    def _fix(self):
        self.panel.Layout()



class ActivityWidget(object):

    def __init__(self, parent, sizer, activity):
        self.parent = parent
        self.activity = activity
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.titleCtrl = wx.StaticText(parent, -1, activity.title)
        self.gaugeCtrl = wx.Gauge(parent, -1, size=(100,10))
        self.gaugeCtrl.Pulse()
        self.msgCtrl = wx.StaticText(parent, -1, "")
        self.lineCtrl = wx.StaticLine(parent, -1)

        flags = wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT
        self.sizer.AddMany([
            (self.titleCtrl, 1, flags, 1),
            (self.gaugeCtrl, 1, flags, 1),
            (self.msgCtrl, 1, flags, 1),
            (self.lineCtrl, 1, flags, 1),
        ])
        sizer.Add(self.sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)


    def update(self, *args, **kwds):

        if 'msg' in kwds:
            self.msgCtrl.SetLabel(kwds['msg'])

        if 'percent' in kwds:
            percent = kwds['percent']
            if percent is None:
                self.gaugeCtrl.Pulse()
            else:
                self.gaugeCtrl.SetValue(percent)


    def destroy(self, sizer):
        self.titleCtrl.Destroy()
        self.msgCtrl.Destroy()
        self.gaugeCtrl.Destroy()
        self.lineCtrl.Destroy()
        sizer.Remove(self.sizer)

