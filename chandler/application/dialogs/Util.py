"""
@copyright: Copyright (c) 2004-2006 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import os, sys, codecs
import wx
from i18n import OSAFMessageFactory as _
from osaf import messages

# A helper method and class for allowing the user to modify an item's attributes
"""
Note: need to migrate translation logic to a base wx dialog class that can
      handle all the work for sub classes
"""

def promptForItemValues(frame, title, item, attrList):
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

    win = ItemValuesDialog(frame, -1, title, item, attrList)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
        # Assign the new values
        win.AssignNewValues()

    win.Destroy()
    return val == wx.ID_OK

class ItemValuesDialog(wx.Dialog):
    def __init__(self, parent, ID, title, item, attrList, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)

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
                 item.getAttributeValue(valueDict["attr"]),
                 wx.DefaultPosition, [400,-1], wx.TE_PASSWORD)
            else:
                text = wx.TextCtrl(self, -1,
                 item.getAttributeValue(valueDict["attr"]),
                 wx.DefaultPosition, [400,-1])
            box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

            sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            textControls.append(text)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK, u" " + messages.OK + u" ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL, u" " + messages.CANCEL + u" ")
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
            self.chandlerItem.setAttributeValue(valueDict["attr"],
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
    win = promptUserDialog(None, -1, title, message, defaultValue)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
       # Assign the new values
       value = win.GetValue()

    else:
       value = None

    win.Destroy()

    return value

def mailError(frame, view, message, account):
    # importing AccountPreferences imports osaf.sharing, but Util is loaded
    # by a sharing dependency, so to avoid import loops, only import
    # AccountPreferences when we need it
    import AccountPreferences
    win = mailErrorDialog(frame, message, account)
    win.CenterOnScreen()
    val = win.ShowModal()

    if val == wx.ID_OK:
       AccountPreferences.ShowAccountPreferencesDialog(frame, account, view)

class mailErrorDialog(wx.Dialog):
    def __init__(self, parent, message, account):

        size = wx.DefaultSize
        pos = wx.DefaultPosition
        style = wx.DEFAULT_DIALOG_STYLE

        self.account = account

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, -1, account.displayName, pos, size, style)

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

        btn = wx.Button(self, wx.ID_CANCEL, u" " + messages.OK + u" ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_OK, _(u" Edit Account Settings "))
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)


class promptUserDialog(wx.Dialog):
    def __init__(self, parent, ID, title, message, value, isPassword=False,
     size=wx.DefaultSize, pos=wx.DefaultPosition,
     style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)

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

        btn = wx.Button(self, wx.ID_OK, u" " +  messages.OK + u" ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL, u" " + messages.CANCEL + u" ")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        # Store these, using attribute names that hopefully wont collide with
        # any wx attributes
        self.textControl = text

    def GetValue(self):
        return self.textControl.GetValue()


def displayLogWindow(frame, logList):

    win = LogWindow(frame, -1, logList)
    win.CenterOnScreen()
    win.ShowModal()
    win.Destroy()

class LogWindow(wx.Dialog):
    def __init__(self, parent, ID, logList, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, "Logs", pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.forClipboard = u""

        for log in logList:
            if not isinstance(log, unicode):
                log = unicode(log, sys.getfilesystemencoding())

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

        btn = wx.Button(self, wx.ID_OK, u" " + messages.OK + u" ")
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


# we really should refactor these dialog methods to get rid of all the
# boilerplate

# A simple "ok/cancel" dialog

def okCancel(parent, caption, message):
    """
    Prompt the user with a Ok/Cancel dialog.  
    Return True if Ok, False if Cancel.
    @param parent: A wx parent
    @type parent: wx frame
    @param caption: The caption string for the dialog
    @type caption: String
    @param message:  A message prompting the user for input
    @type message:  String
    """

    dlg = wx.MessageDialog(parent, message, caption,
     wx.OK | wx.CANCEL | wx.ICON_QUESTION)
    val = dlg.ShowModal()

    if val == wx.ID_OK:
        value = True
    else:
        value = False

    dlg.Destroy()
    return value



# A simple "yes/no" dialog

def ShowMessageDialog(parent, message, caption, flags, resultsTable=None):
    if flags & wx.YES_NO:
        flags |= wx.ICON_QUESTION
    elif flags & wx.OK:
        flags |= wx.ICON_INFORMATION

    if caption is None:
        caption = _(u"Chandler")
        
    dlg = wx.MessageDialog(parent, message, caption, flags)
    val = dlg.ShowModal()
    dlg.Destroy()

    if resultsTable is None:
        return val
    else:
        return resultsTable[val]


def yesNo(parent, caption, message):
    """
    Prompt the user with a Yes/No dialog.
    Return True if Yes, False if No.
    @param parent: A wx parent
    @type parent: wx frame
    @param caption: The caption string for the dialog
    @type caption: String
    @param message:  A message prompting the user for input
    @type message:  String
    """

    return ShowMessageDialog(parent, message, caption,
                             wx.YES_NO, 
                            { wx.ID_YES: True,
                              wx.ID_NO: False })

# A simple yes/no/cancel dialog

def yesNoCancel(parent, caption, message):

    return ShowMessageDialog(parent, message, caption,
                             wx.YES_NO | wx.CANCEL,
                             {wx.ID_YES: True,
                              wx.ID_NO: False,
                              wx.ID_CANCEL: None})

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

def ok(parent, caption, message):
    """
    Display a message dialog with an OK button
    @param parent: A wx parent
    @type parent: wx frame
    @param caption: The caption string for the dialog
    @type caption: String
    @param message:  A message
    @type message:  String
    """
    ShowMessageDialog(parent, message, caption, wx.OK)
