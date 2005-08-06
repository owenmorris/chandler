import os
import wx
import wx.xrc
import application.Globals as Globals

class AccountInfoPromptDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
         resources=None, host=None, path=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.host = host
        self.path = path
        self.resources = resources

        self.mySizer = wx.BoxSizer(wx.VERTICAL)
        self.accountPanel = self.resources.LoadPanel(self, "NewAccountPanel")
        self.mySizer.Add(self.accountPanel, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(self.mySizer)
        self.mySizer.SetSizeHints(self)
        self.mySizer.Fit(self)

        self.textServer = wx.xrc.XRCCTRL(self, "TEXT_SERVERNAME")
        self.textServer.Disable()
        self.textServer.SetValue(host)

        self.textPath = wx.xrc.XRCCTRL(self, "TEXT_SERVERPATH")
        self.textPath.Disable()
        self.textPath.SetValue(path)

        self.textDesc = wx.xrc.XRCCTRL(self, "TEXT_DESCRIPTION")
        wx.EVT_SET_FOCUS(self.textDesc, self.OnFocusGained)
        self.textDesc.SetValue("WebDAV account on %s" % host)

        self.textUsername = wx.xrc.XRCCTRL(self, "TEXT_USERNAME")
        wx.EVT_SET_FOCUS(self.textUsername, self.OnFocusGained)

        self.textPassword = wx.xrc.XRCCTRL(self, "TEXT_PASSWORD")
        wx.EVT_SET_FOCUS(self.textPassword, self.OnFocusGained)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))
        self.textDesc.SetFocus()

    def OnFocusGained(self, evt):
        """ Select entire text field contents when focus is gained. """
        control = evt.GetEventObject()
        wx.CallAfter(control.SetSelection, -1, -1)


    def OnOk(self, evt):
        self.description = self.textDesc.GetValue()
        self.username = self.textUsername.GetValue()
        self.password = self.textPassword.GetValue()
        self.EndModal(True)

    def OnCancel(self, evt):
        self.EndModal(False)

    def GetInfo(self):
        return (self.description, self.username, self.password)



def PromptForNewAccountInfo(parent, host=None, path=None):

    xrcFile = os.path.join(Globals.chandlerDirectory,
        'application', 'dialogs', 'AccountInfoPrompt_wdr.xrc')

    resources = wx.xrc.XmlResource(xrcFile)

    win = AccountInfoPromptDialog(parent, "New Account",
                                  resources=resources, host=host, path=path)

    win.CenterOnScreen()
    val = win.ShowModal()
    if val:
        info = win.GetInfo()
    else:
        info = None
    win.Destroy()
    return info
