import os
import wx
import wx.xrc
import application.Globals
from repository.item.Query import KindQuery
import osaf.contentmodel.mail.Mail as Mail
import application.dialogs.Util
import osaf.framework.sharing.WebDAV as WebDAV
import osaf.framework.sharing.Sharing as Sharing
import application.Parcel
import osaf.current.Current as Current

# Used to lookup the mail model parcel:
MAIL_MODEL = "http://osafoundation.org/parcels/osaf/contentmodel/mail"
# Used to lookup the sharing parcel:
SHARING_MODEL = "http://osafoundation.org/parcels/osaf/framework/sharing"

# Special handlers referenced in the PANELS dictionary below:


def IMAPSaveHandler(item, fields, values):
    newAddressString = values['IMAP_EMAIL_ADDRESS']
    newFullName = values['IMAP_FULL_NAME']
    newUsername = values['IMAP_USERNAME']
    newServer = values['IMAP_SERVER']

    # If either the host or username changes, we need to set this account item
    # to inactive and create a new one.
    if (item.host and item.host != newServer) or (item.username and item.username != newUsername):
        item.isActive = False
        item = Mail.IMAPAccount(view=item.itsView)


    item.replyToAddress = Mail.EmailAddress.getEmailAddress(item.itsView,
                                                            newAddressString,
                                                            newFullName)

    return item # Returning a non-None item tells the caller to continue
                # processing this item.
                # Returning None would tell the caller that processing this 
                # item is complete.



# Used to map form fields to item attributes:
PANELS = {
    "IMAP" : {
        "fields" : {
            "IMAP_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default": "New IMAP account"
            },
            "IMAP_EMAIL_ADDRESS" : {
                "attr" : "emailAddress",
                "type" : "string",
            },
            "IMAP_FULL_NAME" : {
                "attr" : "fullName",
                "type" : "string",
            },
            "IMAP_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "IMAP_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "IMAP_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },
            "IMAP_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 143,
                "required" : True,
            },
            "IMAP_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
                "linkedTo" : ("IMAP_PORT", { True:"993", False:"143" } )
            },
            "IMAP_DEFAULT" : {
                "type" : "currentPointer",
                "pointer" : "IMAPAccount",
                "exclusive" : True,
            },
            "IMAP_SMTP" : {
                "type" : "itemRef",
                "attr" : "defaultSMTPAccount",
                "kind" : "//parcels/osaf/contentmodel/mail/SMTPAccount",
            },
        },
        "id" : "IMAPPanel",
        "saveHandler" : IMAPSaveHandler,
        "displayName" : "IMAP_DESCRIPTION",
        "description" : "Incoming mail (IMAP)",
    },
    "SMTP" : {
        "fields" : {
            "SMTP_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default" : "New SMTP account"
            },
            "SMTP_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "SMTP_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 25,
                "required" : True,
            },
            "SMTP_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
            },
            "SMTP_USE_AUTH" : {
                "attr" : "useAuth",
                "type" : "boolean",
            },
            "SMTP_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "SMTP_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },
        },
        "id" : "SMTPPanel",
        "displayName" : "SMTP_DESCRIPTION",
        "description" : "Outgoing mail (SMTP)",
    },
    "WebDAV" : {
        "fields" : {
            "WEBDAV_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default" : "New WebDAV account"
            },
            "WEBDAV_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "WEBDAV_PATH" : {
                "attr" : "path",
                "type" : "string",
            },
            "WEBDAV_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "WEBDAV_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },
            "WEBDAV_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 80,
                "required" : True,
            },
            "WEBDAV_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
                "linkedTo" : ("WEBDAV_PORT", { True:"443", False:"80" } )
            },
            "WEBDAV_DEFAULT" : {
                "type" : "currentPointer",
                "pointer" : "WebDAVAccount",
                "exclusive" : True,
            },
        },
        "id" : "WebDAVPanel",
        "displayName" : "WEBDAV_DESCRIPTION",
        "description" : "Sharing (WebDAV)",
        "callbacks" : (
            ("WEBDAV_TEST", "OnTestWebDAV"),
        )
    },
}

# Generic defaults based on the attr type.  Use "default" on attr for
# specific defaults.
DEFAULTS = {'string': '', 'integer': 0, 'boolean': False}

class AccountPreferencesDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE, resources=None,
         account=None, view=None):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.resources = resources
        self.view = view

        # outerSizer will have two children to manage: on top is innerSizer,
        # and below that is the okCancelSizer
        self.outerSizer = wx.BoxSizer(wx.VERTICAL)

        # innerSizer will have two children to manage: on the left is the
        # AccountsPanel and on the right is the switchable detail panel
        self.innerSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.accountsPanel = self.resources.LoadPanel(self, "AccountsPanel")
        self.innerSizer.Add(self.accountsPanel, 0, wx.ALIGN_TOP|wx.ALL, 5)
        self.outerSizer.Add(self.innerSizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.okCancelPanel = self.resources.LoadPanel(self, "OkCancelPanel")

        self.outerSizer.Add(self.okCancelPanel, 0,
         wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT|wx.ALL, 5)

        self.panels = {}
        for (key, value) in PANELS.iteritems():
            self.panels[key] = self.resources.LoadPanel(self, value['id'])
            self.panels[key].Hide()

        self.SetSizer(self.outerSizer)
        self.outerSizer.SetSizeHints(self)
        self.outerSizer.Fit(self)

        self.accountsList = wx.xrc.XRCCTRL(self, "ACCOUNTS_LIST")
        self.choiceNewType = wx.xrc.XRCCTRL(self, "CHOICE_NEW_ACCOUNT")

        typeNames = []
        for (key, value) in PANELS.iteritems():
            # store a tuple with account type description, and name
            typeNames.append( (value['description'], key) )
        typeNames.sort()
        for (description, name) in typeNames:
            newIndex = self.choiceNewType.Append(description)
            self.choiceNewType.SetClientData(newIndex, name)
        self.choiceNewType.SetSelection(0)

        self.currentIndex = None # the list index of account in detail panel
        self.currentPanelType = None
        self.currentPanel = None # whatever detail panel we swap in

        # data is a list of dictionaries of the form:
        # 'item' => item.itsUUID
        # 'values' => a dict mapping field names to attribute values
        # 'type' => accountType
        # The order of the data list needs to be the same order as what's in
        # the accounts list widget.
        self.data = [ ]

        self.__PopulateAccountsList(account)

        # If the user deletes an account, its data will be moved here:
        self.deletions = [ ]

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)


        self.Bind(wx.EVT_CHOICE, self.OnNewAccount,
                  id=wx.xrc.XRCID("CHOICE_NEW_ACCOUNT"))
        self.Bind(wx.EVT_BUTTON, self.OnDeleteAccount,
                  id=wx.xrc.XRCID("BUTTON_DELETE"))


        self.Bind(wx.EVT_LISTBOX, self.OnAccountSel,
         id=wx.xrc.XRCID("ACCOUNTS_LIST"))

        self.SetDefaultItem(wx.xrc.XRCCTRL(self, "wxID_OK"))

        # Setting focus to the accounts list let's us "tab" to the first
        # text field (without this, on the mac, tabbing doesn't work)
        self.accountsList.SetFocus()

    def __PopulateAccountsList(self, account):
        """ Find all AccountBase items and put them in the list; also build
            up a data structure with the applicable attribute values we'll
            be editing. If account is passed in, show its details. """

        # Make sure we're sync'ed with any changes other threads have made
        self.view.refresh()

        accountIndex = 0 # which account to select first
        pm = application.Parcel.Manager.get(self.view)
        imapAccountKind = pm.lookup(MAIL_MODEL, "IMAPAccount")
        smtpAccountKind = pm.lookup(MAIL_MODEL, "SMTPAccount")
        webDavAccountKind = pm.lookup(SHARING_MODEL, "WebDAVAccount")

        accounts = []

        for item in KindQuery().run([imapAccountKind]):
            if item.isActive and hasattr(item, 'displayName'):
                accounts.append(item)

        for item in KindQuery().run([smtpAccountKind]):
            if hasattr(item, 'displayName'):
                accounts.append(item)

        for item in KindQuery().run([webDavAccountKind]):
            if hasattr(item, 'displayName'):
                accounts.append(item)

        i = 0
        for item in accounts:
            if account == item:
                accountIndex = i
            values = { }
            for (field, desc) in \
             PANELS[item.accountType]['fields'].iteritems():

                if desc['type'] == 'currentPointer':

                    # See if this item is the current item for the given
                    # pointer name.
                    setting = Current.Current.isCurrent(self.view,
                                                        desc['pointer'], item)

                elif desc['type'] == 'itemRef':
                    try:
                        setting = item.getAttributeValue(desc['attr']).itsUUID
                    except:
                        setting = None

                else:
                    try:
                        setting = item.getAttributeValue(desc['attr'])
                    except AttributeError:
                        try:
                            setting = desc['default']
                        except KeyError:
                            setting = DEFAULTS[desc['type']]

                values[field] = setting
            self.data.append( { "item" : item.itsUUID, "values" : values,
                                "type" : item.accountType } )
            self.accountsList.Append(item.displayName)
            i += 1

        if i > 0:
            self.accountsList.SetSelection(accountIndex)
            self.__SwapDetailPanel(accountIndex)


    def __ApplyChanges(self):
        """ Take the data from the list and apply the values to the items. """

        # First store the current form values to the data structure
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        for account in self.data:
            uuid = account['item']
            if uuid:
                item = self.view.findUUID(account['item'])
            else:
                if account['type'] == "IMAP":
                    item = Mail.IMAPAccount(view=self.view)
                elif account['type'] == "SMTP":
                    item = Mail.SMTPAccount(view=self.view)

                    #XXX: Temp change that checks if no SMTP Account currently
                    #     exists and makes the new account the defaultSMTPAccount
                    #     for the default IMAP ccount

                    if Mail.MailParcel.getSMTPAccount(view=self.view)[0] is None:
                        imapAccount = Mail.MailParcel.getIMAPAccount(view=self.view)

                        if imapAccount is not None:
                            imapAccount.defaultSMTPAccount = item

                elif account['type'] == "WebDAV":
                    item = Sharing.WebDAVAccount(view=self.view)

            values = account['values']
            panel = PANELS[account['type']]

            if panel.has_key("saveHandler"):
                item = panel["saveHandler"](item, panel['fields'], values)

            if item is not None:
                for (field, desc) in panel['fields'].iteritems():

                    if desc['type'] == 'currentPointer':

                        if values[field]:
                            Current.Current.set(self.view, desc['pointer'],
                                                item)

                    elif desc['type'] == 'itemRef':
                        if values[field]:
                            item.setAttributeValue(desc['attr'],
                                             self.view.findUUID(values[field]))

                    else:
                        try:
                            item.setAttributeValue(desc['attr'], values[field])
                        except:
                            pass

    def __ApplyDeletions(self):
        for data in self.deletions:
            uuid = data['item']
            if uuid:
                item = self.view.findUUID(uuid)
                item.delete()

    def __Validate(self):

        # First store the current form values to the data structure
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        i = 0
        for account in self.data:
            uuid = account['item']
            if uuid:
                item = self.view.findUUID(uuid)
            else:
                item = None
            values = account['values']
            panel = PANELS[account['type']]
            if panel.has_key("validationHandler"):
                valid = panel["validationHandler"](item, panel['fields'],
                 values)
                if not valid:
                    # Show the invalid panel
                    self.accountsList.SetSelection(i)
                    self.__SwapDetailPanel(i)
                    return False
            i += 1
        return True

    def __GetDisplayName(self, index):
        data = self.data[self.currentIndex]
        accountType = data['type']
        panel = PANELS[accountType]
        values = self.data[self.currentIndex]['values']
        return values[panel["displayName"]]

    def __SwapDetailPanel(self, index):
        """ Given an index into the account list, store the current panel's
            (if any) contents to the data list, destroy current panel, determine
            type of panel to pull in, load it, populate it. """

        if index == self.currentIndex: return

        if self.currentIndex != None:
            # Get current form data and tuck it away
            self.__StoreFormData(self.currentPanelType, self.currentPanel,
             self.data[self.currentIndex]['values'])
            self.accountsList.SetString(self.currentIndex,
                                        self.__GetDisplayName(self.currentIndex))
            self.innerSizer.Detach(self.currentPanel)
            self.currentPanel.Hide()

        self.currentIndex = index
        self.currentPanelType = self.data[index]['type']
        self.currentPanel = self.panels[self.currentPanelType]
        self.__FetchFormData(self.currentPanelType, self.currentPanel,
         self.data[index]['values'])

        self.innerSizer.Add(self.currentPanel, 0, wx.ALIGN_TOP|wx.ALL, 5)
        self.currentPanel.Show()
        self.innerSizer.Layout()
        self.outerSizer.Layout()
        self.outerSizer.SetSizeHints(self)
        self.outerSizer.Fit(self)

        # When a text field receives focus, call the handler.
        # When an exclusive radio button is clicked, call another handler.
        for field in PANELS[self.currentPanelType]['fields'].keys():
            fieldInfo = PANELS[self.currentPanelType]['fields'][field]
            control = wx.xrc.XRCCTRL(self.currentPanel, field)

            if isinstance(control, wx.TextCtrl):
                wx.EVT_SET_FOCUS(control, self.OnFocusGained)

            elif isinstance(control, wx.RadioButton):
                if fieldInfo.get('exclusive', False):
                    try:
                        # On GTK if you want to have a radio button which can
                        # be set to False, you really need to create a second
                        # radio button and set that guy's value to True, thus
                        # setting the visible button to False:
                        hidden = wx.xrc.XRCCTRL(self.currentPanel,
                                                "%s_HIDDEN" % field)
                        hidden.Hide()
                    except:
                        pass
                    wx.EVT_RADIOBUTTON(control, control.GetId(),
                                       self.OnExclusiveRadioButton)

            elif isinstance(control, wx.CheckBox):
                linkedTo = fieldInfo.get('linkedTo', None)
                if linkedTo is not None:
                    wx.EVT_CHECKBOX(control, control.GetId(),
                                    self.OnLinkedControl)

        for callbackReg in PANELS[self.currentPanelType].get('callbacks', ()):
            self.Bind(wx.EVT_BUTTON, getattr(self, callbackReg[1]),
                      id=wx.xrc.XRCID(callbackReg[0]))


    def __StoreFormData(self, panelType, panel, data):
        for field in PANELS[panelType]['fields'].keys():
            control = wx.xrc.XRCCTRL(panel, field)
            fieldInfo = PANELS[panelType]['fields'][field]
            valueType = fieldInfo['type']
            valueRequired = fieldInfo.get('required', False)
            if valueType == "string":
                val = control.GetValue().strip()
                if valueRequired and not val:
                    continue
            elif valueType == "boolean":
                val = (control.GetValue() == True)
            elif valueType == "currentPointer":
                val = (control.GetValue() == True)
            elif valueType == "itemRef":
                index = control.GetSelection()
                if index == -1:
                    val = None
                else:
                    val = control.GetClientData(index)
            elif valueType == "integer":
                try:
                    val = int(control.GetValue().strip())
                except:
                    # Skip if not valid
                    continue
            data[field] = val

    def __FetchFormData(self, panelType, panel, data):
        for field in PANELS[panelType]['fields'].keys():
            control = wx.xrc.XRCCTRL(panel, field)
            valueType = PANELS[panelType]['fields'][field]['type']
            if valueType == "string":
                control.SetValue(data[field])
            elif valueType == "boolean":
                control.SetValue(data[field])
            elif valueType == "currentPointer":
                try:
                    # On GTK if you want to have a radio button which can
                    # be set to False, you really need to create a second
                    # radio button and set that guy's value to True, thus
                    # setting the visible button to False:
                    if data[field]:
                        control.SetValue(True)
                    else:
                        hidden = wx.xrc.XRCCTRL(panel, "%s_HIDDEN" % field)
                        hidden.SetValue(True)
                except:
                    pass
            elif valueType == "itemRef":
                items = []
                count = 0
                index = -1
                uuid = data[field]
                kind = PANELS[panelType]['fields'][field]['kind']
                for item in KindQuery().run([self.view.findPath(kind)]):
                    if item.isActive:
                        items.append(item)
                        if item.itsUUID == uuid:
                            index = count
                        count += 1

                control.Clear()
                for item in items:
                    newIndex = control.Append(item.displayName)
                    control.SetClientData(newIndex, item.itsUUID)
                if index != -1:
                    control.SetSelection(index)

            elif valueType == "integer":
                control.SetValue(str(data[field]))

    def OnOk(self, evt):
        if self.__Validate():
            self.__ApplyChanges()
            self.__ApplyDeletions()
            self.EndModal(True)
            self.view.commit()

    def OnCancel(self, evt):
        self.EndModal(False)

    def OnNewAccount(self, evt):

        selection = self.choiceNewType.GetSelection()
        if selection == 0:
            return

        accountType = self.choiceNewType.GetClientData(selection)
        self.choiceNewType.SetSelection(0)

        accountName = "New %s account" % accountType

        values = { }

        for (field, desc) in PANELS[accountType]['fields'].iteritems():

            if desc['type'] == 'currentPointer':
                setting = False

            elif desc['type'] == 'itemRef':
                setting = None

            else:
                try:
                    setting = desc['default']
                except KeyError:
                    setting = DEFAULTS[desc['type']]

            values[field] = setting

        self.data.append( { "item" : None,
                            "values" : values,
                            "type" : accountType } )

        index = self.accountsList.Append(accountName)
        self.accountsList.SetSelection(index)
        self.__SwapDetailPanel(index)

    def OnDeleteAccount(self, evt):
        index = self.accountsList.GetSelection()
        self.accountsList.Delete(index)
        self.deletions.append(self.data[index])
        del self.data[index]
        self.innerSizer.Detach(self.currentPanel)
        self.currentPanel.Hide()
        self.currentIndex = None
        self.accountsList.SetSelection(0)
        self.__SwapDetailPanel(0)

    def OnTestWebDAV(self, evt):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        host = data['WEBDAV_SERVER']
        port = data['WEBDAV_PORT']
        useSSL = data['WEBDAV_USE_SSL']
        username = data['WEBDAV_USERNAME']
        password = data['WEBDAV_PASSWORD']
        path = data['WEBDAV_PATH']
        access = WebDAV.checkAccess(host, port=port, useSSL=useSSL,
                                    username=username, password=password,
                                    path=path)
        result = access[0]
        reason = access[1]

        if result == WebDAV.CANT_CONNECT:
            msg = "Couldn't connect to server '%s'.\nPlease double-check the server name and port settings." % host
            msg += "\nError was: '%s'." % reason
        elif result == WebDAV.NO_ACCESS:
            msg = "Permission denied by server '%s'." % host
        elif result == WebDAV.READ_ONLY:
            msg = "You have read access but not write access."
        elif result == WebDAV.READ_WRITE:
            msg = "Test was successful.\nThis account has read/write access."
        else:
            # This shouldn't happen
            msg = "Test failed with an unknown response."

        application.dialogs.Util.ok(self, "WebDAV Test Results", msg)


    def OnAccountSel(self, evt):
        # Huh? This is always False!
        # if not evt.IsSelection(): return

        sel = evt.GetSelection()
        self.__SwapDetailPanel(sel)

    def OnFocusGained(self, evt):
        """ Select entire text field contents when focus is gained. """
        control = evt.GetEventObject()
        wx.CallAfter(control.SetSelection, -1, -1)

    def OnLinkedControl(self, evt):
        control = evt.GetEventObject()

        # Determine current panel
        panel = PANELS[self.currentPanelType]

        # Scan through fields, seeing if this control corresponds to one
        # If marked as linkedTo, change the linked field
        ##        "linkedTo" : ("IMAP_PORT", { True:993, False:143 } )
        for (field, fieldInfo) in panel['fields'].iteritems():
            if wx.xrc.XmlResource.GetXRCID(field) == control.GetId():
                linkedTo = fieldInfo.get('linkedTo', None)
                if linkedTo is not None:
                    linkedField = linkedTo[0]
                    linkedValues = linkedTo[1]
                    linkedControl = wx.xrc.XRCCTRL(self.currentPanel,
                                                   linkedField)
                    if linkedControl.GetValue() in (linkedValues.values()):
                        linkedControl.SetValue(linkedValues[control.GetValue()])
                break

    def OnExclusiveRadioButton(self, evt):
        """ When an exclusive attribute (like default) is set on one account,
            set that attribute to False on all other accounts of the same kind.
        """
        control = evt.GetEventObject()

        # Determine current panel
        # Scan through fields, seeing if this control corresponds to one
        # If marked as exclusive, set all other accounts of this type to False
        panel = PANELS[self.currentPanelType]
        for (field, fieldInfo) in panel['fields'].iteritems():
            if wx.xrc.XmlResource.GetXRCID(field) == control.GetId():
                if fieldInfo.get('exclusive', False):
                    index = 0
                    for accountData in self.data:
                        if accountData['type'] == self.currentPanelType:
                            if index != self.currentIndex:
                                accountData['values'][field] = False
                        index += 1
                    break


def ShowAccountPreferencesDialog(parent, account=None, view=None):
        xrcFile = os.path.join(application.Globals.chandlerDirectory,
         'application', 'dialogs', 'AccountPreferences_wdr.xrc')
        resources = wx.xrc.XmlResource(xrcFile)
        win = AccountPreferencesDialog(parent, "Account Preferences",
         resources=resources, account=account, view=view)
        win.CenterOnScreen()
        val = win.ShowModal()
        win.Destroy()
        return val
