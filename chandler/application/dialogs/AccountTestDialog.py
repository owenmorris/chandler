#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

import wx
from application import Globals
from i18n import ChandlerMessageFactory as _
from osaf.mail import constants, errors

class TestAccountSettingsDialog(wx.Dialog):
    def __init__(self, accountType, account):
        super(TestAccountSettingsDialog, self).__init__(None, -1)

        self.accountType = accountType
        self.account = account

        self.Title = _(u"Testing %(accountType)s Account '%(accountName)s'") % \
                          {'accountType': accountType, 'accountName': account.displayName}

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.progressPanel = ProgressPanel(self, constants.TESTING_TIMEOUT * 1000)
        self.buttonPanel = ButtonPanel(self)
        self.resultsPanel = None
        self.resultsButtonPanel = None
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        #Signals that a testing of an account is in progress
        self.inProgress = False

        #Signals that a try again button request was executed
        self.tryAgain = False

        #The IMAP, POP, or SMTP client
        self.mailInstance = None

        self.initDialog()
        self.CenterOnScreen()
        self.ShowModal()

    def initDialog(self):
        if self.tryAgain:
            self.resultsPanel.Hide()
            self.sizer.Detach(self.resultsPanel)
            self.resultsPanel = None

            self.resultsButtonPanel.Hide()
            self.sizer.Detach(self.resultsButtonPanel)
            self.resultsButtonPanel = None

            self.progressPanel.Show(True)
            self.buttonPanel.Show(True)

        self.sizer.Add(self.progressPanel, 0, wx.GROW|wx.ALL, 5)
        self.sizer.Add(self.buttonPanel, 1,wx.ALIGN_RIGHT|wx.ALL, 5)

        self.progressPanel.initDialog()

        if self.tryAgain:
            resizeLayout(self, self.sizer)
        else:
            initLayout(self, self.sizer)

        if self.mailInstance is None:
            m = getattr(Globals.mailService, "get%sInstance" % self.accountType)
            assert(m is not None)
            self.mailInstance = m(self.account)

        self.mailInstance.testAccountSettings(self.OnTestComplete)

        self.inProgress = True
        self.tryAgain = False

    def connectionTimeout(self):
        if self.inProgress:
            self.mailInstance.cancelLastRequest()
            self.OnTestComplete((0, errors.STR_CONNECTION_ERROR))

    def OnTryAgain(self, evt):
        self.tryAgain = True
        self.initDialog()

    def OnClose(self, evt):
        if self.inProgress:
            self.progressPanel.timer.Stop()
            self.mailInstance.cancelLastRequest()

        self.EndModal(True)
        self.Destroy()

    def OnTestComplete(self, results):
        self.inProgress = False
        self.progressPanel.timer.Stop()
        self.progressPanel.Hide()
        self.sizer.Detach(self.progressPanel)

        self.buttonPanel.Hide()
        self.sizer.Detach(self.buttonPanel)

        err = results[1]

        self.resultsPanel = ResultsPanel(self, err)
        self.sizer.Add(self.resultsPanel, 0, wx.GROW|wx.ALL, 5)

        self.resultsButtonPanel = ResultsButtonPanel(self, err)
        self.sizer.Add(self.resultsButtonPanel, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        resizeLayout(self, self.sizer)

class ProgressPanel(wx.Panel):
    def __init__(self, parent, gaugeTime):
        super(ProgressPanel, self).__init__(parent, -1)
        self.dialog = parent

        self.progress = 0
        self.timeout = gaugeTime
        self.boldFont = wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD)

        txt = _(u"Connecting to server '%(hostName)s'") % {'hostName': self.dialog.account.host}

        self.label = wx.StaticText(self, -1, txt, size=(450,-1))
        self.label.SetFont(self.boldFont)
        self.gauge = wx.Gauge(self, -1, gaugeTime, size=(400, 25))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.label, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        self.sizer.Add(self.gauge, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        self.timer = wx.Timer(self, 0)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        initLayout(self, self.sizer)
        self.initDialog()

    def initDialog(self):
        self.progress = 0
        self.gauge.SetValue(self.progress)
        self.timer.Start(250)

    def OnTimer(self, evt):
        self.progress += 250

        if self.progress >= self.timeout:
            self.dialog.connectionTimeout()
            return

        self.gauge.SetValue(self.progress)


class ResultsPanel(wx.Panel):
    def __init__(self, parent, err=None):
        super(ResultsPanel, self).__init__(parent, -1)
        self.dialog = parent
        self.boldFont = wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD)

        if err:
            txt = _(u"The server '%(hostName)s' raised the following error:\n\n\t%(errText)s") % \
                        {'hostName': self.dialog.account.host, 'errText': err}
        else:
            txt = _(u"Connection to server '%(hostName)s' was successful.") % \
                    {'hostName': self.dialog.account.host}

        self.label = wx.StaticText(self, -1, txt, size=(450, 100))
        self.label.SetFont(self.boldFont)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.label, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        initLayout(self, self.sizer)

class ButtonPanel(wx.Panel):
    def __init__(self, parent):
        super(ButtonPanel, self).__init__(parent, -1)
        self.dialog = parent

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        #XXX could try WX_ID_CANCEL and see what happens for localization
        #self.mainButton = wx.Button(self, -1, _(u"Cancel"))
        self.mainButton = wx.Button(self, wx.ID_CANCEL)
        self.mainButton.Bind(wx.EVT_BUTTON, self.dialog.OnClose)

        self.sizer.Add(self.mainButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        initLayout(self, self.sizer)

class ResultsButtonPanel(wx.Panel):
    def __init__(self, parent, failed):
        super(ResultsButtonPanel, self).__init__(parent, -1)
        self.dialog = parent

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        if failed:
            self.tryAgainButton = wx.Button(self, -1, _(u"Try Again"))
            self.tryAgainButton.Bind(wx.EVT_BUTTON, self.dialog.OnTryAgain)
            self.sizer.Add(self.tryAgainButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.mainButton = wx.Button(self, -1)
        self.mainButton.SetLabel(_(u"Close Window"))
        self.mainButton.SetDefault()
        self.mainButton.Bind(wx.EVT_BUTTON, self.dialog.OnClose)

        self.sizer.Add(self.mainButton, 1, wx.ALIGN_RIGHT|wx.ALL, 5)

        initLayout(self, self.sizer)

def initLayout(container, sizer):
    container.SetSizer(sizer)
    container.SetAutoLayout(True)
    resizeLayout(container, sizer)

def resizeLayout(container, sizer):
    sizer.Layout()
    sizer.SetSizeHints(container)
    sizer.Fit(container)
