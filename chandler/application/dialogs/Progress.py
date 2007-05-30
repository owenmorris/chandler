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
import threading
from i18n import ChandlerMessageFactory as _
from osaf.activity import *


def Show(activity):
    win = ProgressFrame(None, -1, activity.title,
        size=(300,100), style=wx.DEFAULT_FRAME_STYLE,
        activity=activity)
    win.Show()



class ProgressFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        self.activity = kwds['activity']
        del kwds['activity']
        super(ProgressFrame, self).__init__(*args, **kwds)
        self.listener = Listener(activity=self.activity, callback=self.callback)
        self.widgets = { }

        self.panel = wx.Panel(self, -1)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.gaugeCtrl = wx.Gauge(self, -1, size=(100,10))
        self.sizer.Add(self.gaugeCtrl, 0,
            wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        self.gaugeCtrl.Pulse()

        self.msgCtrl = wx.StaticText(self, -1, "")
        self.sizer.Add(self.msgCtrl, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.cancelCtrl = wx.Button(self, wx.ID_CANCEL)
        self.sizer.Add(self.cancelCtrl, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.sizer.Layout()

        self.cancel = False

    def OnCloseWindow(self, event):
        self.listener.unregister()
        self.Destroy()

    def OnCancel(self, event):
        self.cancel = True

    def callback(self, activity, *args, **kwds):
        # Can be called from any thread; will call _callback in main thread

        if threading.currentThread().getName() != "MainThread":
            wx.GetApp().PostAsyncEvent(self._callback, activity, *args, **kwds)
        else:
            self._callback(activity, *args, **kwds)

        return self.cancel


    def _callback(self, activity, *args, **kwds):
        # Must be called in main thread

        if 'status' in kwds:
            status = kwds['status']
            if status in (STATUS_ABORTED, STATUS_FAILED, STATUS_COMPLETE):
                self.OnCloseWindow(None)
                return

        self.updateWidget(activity, *args, **kwds)

    def updateWidget(self, activity, *args, **kwds):
        if 'msg' in kwds:
            self.msgCtrl.SetLabel(kwds['msg'])

        if 'percent' in kwds:
            percent = kwds['percent']
            if percent is None:
                self.gaugeCtrl.Pulse()
            else:
                self.gaugeCtrl.SetValue(percent)

        wx.Yield()
