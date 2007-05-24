#   Copyright (c) 2004-2007 Open Source Applications Foundation
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


import os, codecs
import wx
from i18n import ChandlerMessageFactory as _

# A helper method and class for allowing the user to modify an item's attributes
"""
Note: need to migrate translation logic to a base wx dialog class that can
      handle all the work for sub classes
"""

def promptForItemValues(title, item, attrList):
    """
    Given an item and a list of attributes, display a modal dialog with
    a text field per attribute, with each field populated directly from
    the item's attribute values.  If the user OK's the dialog, the new
    values are applied to the item's attributes.

    @param frame: A wx parent frame
    @type frame: wx frame
    @param title: The title string for the dialog
    @type title: String
    @param item:  A chandler item
    @type item:  Item
    @param attrList: A list of dictionaries, each one having the following
     keys::

        "attr": an attribute name
        "label": a label to display for the field
        "password": an optional key, set to True if you want this field to
                    be displayed like a password (with asterisks)

    """

    win = ItemValuesDialog(title, item, attrList)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
        # Assign the new values
        win.AssignNewValues()

    win.Destroy()
    return val == wx.ID_OK

class ItemValuesDialog(wx.Dialog):
    def __init__(self, title, item, attrList, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(None, -1, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        textControls = []
        for valueDict in attrList:
            box = wx.BoxSizer(wx.HORIZONTAL)

            label = wx.StaticText(self, -1, valueDict["label"])
            box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            if valueDict.get("password", False):
                text = wx.TextCtrl(self, -1,
                 getattr(item, valueDict["attr"]),
                 wx.DefaultPosition, [400,-1], wx.TE_PASSWORD)
            else:
                text = wx.TextCtrl(self, -1,
                 getattr(item, valueDict["attr"]),
                 wx.DefaultPosition, [400,-1])
            box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

            sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            textControls.append(text)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.chandlerTextControls = textControls
        self.chandlerItem = item
        self.chandlerAttrs = attrList

    def AssignNewValues(self):
        i = 0
        for (valueDict) in self.chandlerAttrs:
            setattr(self.chandlerItem, valueDict["attr"],
                    self.chandlerTextControls[i].GetValue())
            i += 1


# A simple "prompt-the-user-for-a-string" dialog

def promptUser(title, message, defaultValue=""):
    """
    Prompt the user to enter in a string.  Return None if cancel is hit.

    @param title: The title string for the dialog
    @type title: String
    @param message:  A message prompting the user for input
    @type message:  String
    @param defaultValue:  A value to populate the text field with
    @type defaultValue:  String
    """
    win = promptUserDialog(title, message, defaultValue)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
       # Assign the new values
       value = win.GetValue()

    else:
       value = None

    win.Destroy()

    return value

def mailAccountError(view, message, account):
    # importing AccountPreferences imports osaf.sharing, but Util is loaded
    # by a sharing dependency, so to avoid import loops, only import
    # AccountPreferences when we need it
    import AccountPreferences
    win = MailAccountErrorDialog(message)
    win.CenterOnScreen()
    val = win.ShowModal()

    win.Destroy()

    if val == wx.ID_OK:
       AccountPreferences.ShowAccountPreferencesDialog(account, view)


def mailAddressError():
    message = _(u"You have addressed this message to invalid email addresses.")
    win = MailAddressErrorDialog(message)
    win.CenterOnScreen()
    val = win.ShowModal()

    win.Destroy()

    if val == wx.ID_OK:
        return False

    return True

class MailErrorBaseDialog(wx.Dialog):
    def __init__(self, message):
        size = wx.DefaultSize
        pos = wx.DefaultPosition
        style = wx.DEFAULT_DIALOG_STYLE

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(None, -1, _(u"Mail Error"), pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, message)
        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 55)

        box = wx.BoxSizer(wx.HORIZONTAL)

        self.addButtons(box)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def addButtons(self, sizer):
        raise NotImplementedError()

class MailAccountErrorDialog(MailErrorBaseDialog):
    def addButtons(self, sizer):
        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetDefault()
        sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_OK, _(u" Edit Account Settings "))
        sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)


class MailAddressErrorDialog(MailErrorBaseDialog):
    def addButtons(self, sizer):
        btn = wx.Button(self, wx.ID_CANCEL, _(u"Fix email addresses"))
        btn.SetDefault()
        sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_OK, _(u"Send anyway"))
        sizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)


class promptUserDialog(wx.Dialog):
    def __init__(self, title, message, value, isPassword=False,
     size=wx.DefaultSize, pos=wx.DefaultPosition,
     style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(None, -1, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, message)
        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        if isPassword:
            text = wx.TextCtrl(self, -1, value, wx.DefaultPosition, [500,-1],
             wx.TE_PASSWORD)
        else:
            text = wx.TextCtrl(self, -1, value, wx.DefaultPosition, [500,-1])

        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        # sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.textControl = text
        text.SetFocus()

    def GetValue(self):
        return self.textControl.GetValue()


class checkboxUserDialog(wx.Dialog):
    def __init__(self, parent, title, message, value,
     size=wx.DefaultSize, pos=wx.DefaultPosition,
     style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, -1, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, message)
        label.Wrap(400)
        sizer.Add(label, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        # [ [ checkboxctrl ]        [ buttonctrl buttonctr ] ]

        row = wx.BoxSizer(wx.HORIZONTAL)

        box = wx.BoxSizer(wx.HORIZONTAL)

        checkbox = wx.CheckBox(self, -1, value, wx.DefaultPosition)

        box.Add(checkbox, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        row.Add(box, 1, wx.ALIGN_LEFT|wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        # sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_YES)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_NO)
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        row.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        sizer.Add(row, 0, wx.GROW|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.checkbox = checkbox
        #if wx.Platform != '__WXMAC__':
        #    checkbox.SetFocus()

        self.Bind(wx.EVT_BUTTON, self.End, id=wx.ID_YES)
        self.Bind(wx.EVT_BUTTON, self.End, id=wx.ID_NO)

    def End(self, event):
        self.EndModal(event.GetId())

    def GetValue(self):
        return self.checkbox.GetValue()


def displayLogWindow(logList):

    win = LogWindow(logList)
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()

class LogWindow(wx.Dialog):
    def __init__(self, logList, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(None, -1, "Logs", pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.forClipboard = u""

        for log in logList:
            if not isinstance(log, unicode):
                log = unicode(log, 'utf8')

            f = codecs.open(log, encoding='utf-8', mode="r", errors="ignore")
            #combined is a list of unicode text
            combined = u"".join(f.readlines()[-500:])
            label = wx.StaticText(self, -1, log)
            sizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

            self.forClipboard += u"==> %s <==\n\n" % log

            text = wx.TextCtrl(self, -1,
             combined,
             pos=wx.DefaultPosition, size=[800,200], style=wx.TE_MULTILINE)
            text.ShowPosition(text.GetLastPosition())
            self.forClipboard += u"%s\n\n" % combined

            sizer.Add(text, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _(u"Copy to Clipboard"))
        self.Bind(wx.EVT_BUTTON, self.OnCopy, id=btn.GetId())
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def OnCopy(self, evt):
        gotClipboard = wx.TheClipboard.Open()
        if gotClipboard:
            wx.TheClipboard.SetData(wx.TextDataObject(self.forClipboard))
            wx.TheClipboard.Close()


def displayI18nManagerDebugWindow():
    import i18n
    win = DebugWindow(u"I18nManager Resource Debugger",
                      i18n._I18nManager.getDebugString())
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()

def displayAddressDebugWindow(view, type=1):
    from application import schema

    # Types:
    # =========
    # 1: meEmailAddressCollection
    # 2: currentMeEmailAddresses
    # 3: currenMeEmailAddress

    list = []

    if type == 1:
        collection = schema.ns("osaf.pim", view).meEmailAddressCollection
    elif type == 2:
        collection = schema.ns('osaf.pim', view).currentMeEmailAddresses.item.emailAddresses
    else:
        collection = [schema.ns('osaf.pim', view).currentMeEmailAddress.item]

    for eAddr in collection:
        if eAddr:
            list.append(eAddr.emailAddress)

    win = DebugWindow(u"Email Address Debugger",
                      u'\n'.join(list), tsize=[400,300])

    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()

class DebugWindow(wx.Dialog):
    def __init__(self, title, text, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
           tsize=[600,500]):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(None, -1, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        txt = wx.TextCtrl(self, -1, text,
               pos=wx.DefaultPosition, size=tsize,
               style=wx.TE_MULTILINE)

        txt.SetEditable(False)

        txt.ShowPosition(txt.GetLastPosition())

        sizer.Add(txt, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1),
                            style=wx.LI_HORIZONTAL)

        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)


# we really should refactor these dialog methods to get rid of all the
# boilerplate

# A simple "yes/no" dialog

def ShowMessageDialog(message, caption, flags, resultsTable=None,
                      textTable=None):
    if flags & wx.YES_NO:
        flags |= wx.ICON_QUESTION
    elif flags & wx.OK:
        flags |= wx.ICON_INFORMATION

    if caption is None:
        caption = _("Chandler")

    if textTable is not None:
        dlg = CustomYesNoLabelDialog(message, caption, flags, textTable)
    else:
        dlg = wx.MessageDialog(None, message, caption, flags)

    val = dlg.ShowModal()
    dlg.Destroy()

    if resultsTable is None:
        return val
    else:
        return resultsTable[val]

class CustomYesNoLabelDialog(wx.Dialog):
    def __init__(self, message, caption, flags, textTable):
        
        wx.Dialog.__init__(self, None, -1, caption)
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(self, -1, message)
        text.Wrap(300)
        outerSizer.Add(text, 0, wx.ALIGN_CENTER|wx.ALL, 20)

        sizer = wx.StdDialogButtonSizer()
        if flags & wx.YES_NO:
            sizer.AddButton(wx.Button(self, wx.ID_YES))
            sizer.AddButton(wx.Button(self, wx.ID_NO))
        elif flags & wx.OK:
            sizer.AddButton(wx.Button(self, wx.ID_OK))
            
        if flags & wx.CANCEL:
            sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        
        sizer.Realize()
        for id, text in textTable.iteritems():
            self.FindWindowById(id).SetLabel(text)        
        
        outerSizer.Add(sizer, 0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 10)

        self.SetSizer(outerSizer)
        outerSizer.Fit(self)
        
        if flags & wx.YES_NO:
            self.Bind(wx.EVT_BUTTON, self.End, id=wx.ID_YES)
            self.Bind(wx.EVT_BUTTON, self.End, id=wx.ID_NO)
        elif flags & wx.OK:
            self.Bind(wx.EVT_BUTTON, self.End, id=wx.ID_OK)
            
        if flags & wx.CANCEL:
            self.Bind(wx.EVT_BUTTON, self.End, id=wx.ID_CANCEL) 

    def End(self, event):
        self.EndModal(event.GetId())

# A simple file selection dialog

def showFileDialog(parent, message, defaultDir, defaultFile, wildcard, style):
    if defaultDir is None:
        defaultDir = u""

    dlg = wx.FileDialog(parent, message, unicode(defaultDir), unicode(defaultFile),
                        wildcard, style)

    """
    Blocking call
    """
    cmd = dlg.ShowModal()
    (dir, filename) = os.path.split(dlg.GetPath())
    dlg.Destroy()

    return (cmd, dir, filename)

# A simple alert dialog

class ProgressDialog(wx.Dialog):
    ERROR                 = 0
    SUCCESS               = 1
    CERT_DIALOG_DISPLAYED = 2

    TIMEOUT               = 10
    DISPLAY_YES_NO        = False
    APPLY_SETTINGS        = False
    ALLOW_CANCEL          = True
    SUCCESS_TEXT_SIZE     = (450, 100)
    ERROR_TEXT_SIZE       = (450, 100)

    def __init__(self, parent):
        st = wx.DEFAULT_DIALOG_STYLE

        if not self.ALLOW_CANCEL:
            # Turn of the ability for the
            # user to close the dialog
            # manually
            st = st & ~wx.CLOSE_BOX

        super(ProgressDialog, self).__init__(parent, -1, self.getTitleText(),
                                             style=st)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.progressPanel = ProgressPanel(self, self.TIMEOUT * 1000)
        self.buttonPanel = ButtonPanel(self)
        self.resultsPanel = None
        self.resultsButtonPanel = None

        if self.ALLOW_CANCEL:
            self.Bind(wx.EVT_CLOSE, self.OnClose)

        #Signals that operations are in progress
        self.inProgress = False

        #Signals that the try again button clicked
        self.tryAgain = False

    def initDialog(self):
        #    custom logic
        self.layoutDialog()
        self.CenterOnParent()
        self.ShowModal()

    def layoutDialog(self):
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

        self.progressPanel.layoutDialog()

        if self.tryAgain:
            resizeLayout(self, self.sizer)
        else:
            initLayout(self, self.sizer)

        self.inProgress = True
        self.tryAgain = False

        # Callback to be implemented in
        # the child class
        self.performAction()

    def connectionTimeout(self):
        if self.inProgress:
            self.cancelAction()
            self.OnActionComplete((0, self.getTimeoutText()))

    def OnTryAgain(self, evt):
        self.tryAgain = True
        self.layoutDialog()

    def OnClose(self, evt):
        if self.inProgress:
            self.progressPanel.timer.Stop()
            self.cancelAction()

        self.EndModal(True)
        self.Destroy()

    def OnSuccess(self, value):
        # Override to provide
        # success handling logic
        return

    def OnError(self, value):
        # Override to provide
        # error handling logic
        return

    def OnActionComplete(self, results):
        self.inProgress = False

        self.progressPanel.timer.Stop()
        self.progressPanel.Hide()
        self.sizer.Detach(self.progressPanel)

        self.buttonPanel.Hide()
        self.sizer.Detach(self.buttonPanel)

        statusCode, statusValue = results

        if statusCode == self.CERT_DIALOG_DISPLAYED:
            # The SSL Cert Dialog was displayed
            # So close this progress dialog
            # If the user selects to accept
            # the cert the SSL code will
            # create a new instance of this
            # dialog via reconnect method
            return self.OnClose(1)

        if statusCode == self.SUCCESS:
            self.OnSuccess(statusValue)

        elif statusCode == self.ERROR:
            self.OnError(statusValue)

        self.resultsPanel = ResultsPanel(self, statusCode, statusValue)
        self.sizer.Add(self.resultsPanel, 0, wx.GROW|wx.ALL, 5)

        self.resultsButtonPanel = ResultsButtonPanel(self, statusCode)
        self.sizer.Add(self.resultsButtonPanel, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        resizeLayout(self, self.sizer)

    def performAction(self):
        raise NotImplementedError()

    def cancelAction(self):
        raise NotImplementedError()

    def getTimeoutText(self):
        raise NotImplementedError()

    def getTitleText(self):
        raise NotImplementedError()

    def getStartText(self):
        raise NotImplementedError()

    def getSuccessText(self, statusValue):
        raise NotImplementedError()

    def getErrorText(self, statusValue):
        raise NotImplementedError()

    def OnYes(self, evt):
        raise NotImplementedError()


class ProgressPanel(wx.Panel):
    def __init__(self, parent, gaugeTime):
        super(ProgressPanel, self).__init__(parent, -1)
        self.parent = parent

        self.progress = 0
        self.timeout = gaugeTime

        self.label = wx.StaticText(self, -1, self.parent.getStartText(),
                                   size=(450,-1))

        self.gauge = wx.Gauge(self, -1, gaugeTime, size=(400, 25))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.label, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        self.sizer.Add(self.gauge, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        self.timer = wx.Timer(self, 0)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        initLayout(self, self.sizer)
        self.layoutDialog()

    def layoutDialog(self):
        self.progress = 0
        self.gauge.SetValue(self.progress)
        self.timer.Start(250)

    def OnTimer(self, evt):
        self.progress += 250

        if self.progress >= self.timeout:
            self.parent.connectionTimeout()
            return

        self.gauge.SetValue(self.progress)

class ResultsPanel(wx.Panel):
    def __init__(self, parent, statusCode, statusValue):
        super(ResultsPanel, self).__init__(parent, -1)
        self.parent = parent

        if statusCode == self.parent.ERROR:
            txt = self.parent.getErrorText(statusValue)
            sz  = self.parent.ERROR_TEXT_SIZE

        elif statusCode == self.parent.SUCCESS:
            txt = self.parent.getSuccessText(statusValue)
            sz  = self.parent.SUCCESS_TEXT_SIZE

        else:
            # This code should never be reached
            raise Exception("Invalid status code passed")

        self.label = wx.StaticText(self, -1, txt, size=sz)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.label, 0, wx.ALIGN_LEFT|wx.ALL, 10)
        initLayout(self, self.sizer)

class ButtonPanel(wx.Panel):
    def __init__(self, parent):
        super(ButtonPanel, self).__init__(parent, -1)
        self.parent = parent

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.parent.ALLOW_CANCEL:
            self.mainButton = wx.Button(self, wx.ID_CANCEL)
            self.mainButton.Bind(wx.EVT_BUTTON, self.parent.OnClose)

            self.sizer.Add(self.mainButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        initLayout(self, self.sizer)

class ResultsButtonPanel(wx.Panel):
    def __init__(self, parent, statusCode):
        super(ResultsButtonPanel, self).__init__(parent, -1)
        self.parent = parent

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        if statusCode == self.parent.ERROR:
            self.tryAgainButton = wx.Button(self, -1, _(u"Try Again"))
            self.tryAgainButton.Bind(wx.EVT_BUTTON, self.parent.OnTryAgain)
            self.sizer.Add(self.tryAgainButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

            self.closeButton = wx.Button(self, -1, _(u"Close Window"))
            self.closeButton.SetDefault()
            self.closeButton.Bind(wx.EVT_BUTTON, self.parent.OnClose)
            self.sizer.Add(self.closeButton, 1, wx.ALIGN_RIGHT|wx.ALL, 5)

        elif self.parent.DISPLAY_YES_NO == True:
            self.noButton = wx.Button(self, wx.ID_NO)
            self.noButton.Bind(wx.EVT_BUTTON, self.parent.OnClose)
            self.sizer.Add(self.noButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

            self.yesButton = wx.Button(self, wx.ID_YES)
            self.yesButton.SetDefault()
            self.yesButton.Bind(wx.EVT_BUTTON, self.parent.OnYes)
            self.sizer.Add(self.yesButton, 1, wx.ALIGN_RIGHT|wx.ALL, 5)

        elif self.parent.APPLY_SETTINGS == True:
            self.cButton = wx.Button(self, wx.ID_CANCEL)
            self.cButton.Bind(wx.EVT_BUTTON, self.parent.OnClose)
            self.sizer.Add(self.cButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

            self.aButton = wx.Button(self, -1, _(u"Apply settings"))
            self.aButton.SetDefault()
            self.aButton.Bind(wx.EVT_BUTTON, self.parent.OnApplySettings)
            self.sizer.Add(self.aButton, 1, wx.ALIGN_RIGHT|wx.ALL, 5)

        else:
            self.closeButton = wx.Button(self, -1, _(u"Close Window"))
            self.closeButton.SetDefault()
            self.closeButton.Bind(wx.EVT_BUTTON, self.parent.OnClose)
            self.sizer.Add(self.closeButton, 1, wx.ALIGN_RIGHT|wx.ALL, 5)

        initLayout(self, self.sizer)

def initLayout(container, sizer):
    container.SetSizer(sizer)
    container.SetAutoLayout(True)
    resizeLayout(container, sizer)

def resizeLayout(container, sizer):
    sizer.Layout()
    sizer.SetSizeHints(container)
    sizer.Fit(container)
