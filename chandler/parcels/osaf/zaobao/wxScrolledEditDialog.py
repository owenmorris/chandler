from wxPython import wx
from wxPython.lib.layoutf import Layoutf

#----------------------------------------------------------------------
class wxScrolledMessageDialog(wx.wxDialog):
    def __init__(self, parent, msg, caption, pos = wx.wxDefaultPosition, size = (500,300)):
        wx.wxDialog.__init__(self, parent, -1, caption, pos, size)
        x, y = pos
        if x == -1 and y == -1:
            self.CenterOnScreen(wx.wxBOTH)
        self.text = wx.wxTextCtrl(self, -1, msg, wx.wxDefaultPosition,
                             wx.wxDefaultSize,
                             wx.wxTE_MULTILINE)
        ok = wx.wxButton(self, wx.wxID_OK, "OK")
        cancel = wx.wxButton(self, wx.wxID_CANCEL, "Cancel")
        self.text.SetConstraints(Layoutf('t=t5#1;b=t5#2;l=l5#1;r=r5#1', (self,ok,cancel)))
        ok.SetConstraints(Layoutf('b=b5#1;x%w25#1;w!80;h!25', (self,)))
        cancel.SetConstraints(Layoutf('b=b5#1;x%w75#1;w!80;h!25', (self,)))
        self.SetAutoLayout(1)
        self.Layout()

def scrolledEditDialog(parent=None, message='', title='', pos=wx.wxDefaultPosition, size=(500,300)):
    dialog = wxScrolledMessageDialog(parent, message, title, pos, size)
    result = None
    if (dialog.ShowModal() == wx.wxID_OK):
            result = dialog.text.GetValue().encode('ascii')
    dialog.Destroy()
    return result
