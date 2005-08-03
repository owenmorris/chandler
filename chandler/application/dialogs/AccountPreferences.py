# Account Preferences Dialog
# Invoke this using the ShowAccountPreferencesDialog() method

import os
import wx
import wx.xrc

import application.schema as schema
import application.Globals
import application.Parcel
import application.dialogs.Util
import osaf.contentmodel.mail as Mail
import osaf.framework.sharing.WebDAV as WebDAV
import osaf.framework.sharing.Sharing as Sharing


# Special handlers referenced in the PANELS dictionary below:

def IMAPValidationHandler(item, fields, values):
    newAddressString = values['IMAP_EMAIL_ADDRESS']
    # Blank address string?  Don't bother the user now, they will get
    # reminded when they actually try to fetch mail.  Bogus address?
    # They better fix it before leaving the dialog box.
    if not newAddressString or \
        Mail.EmailAddress.isValidEmailAddress(newAddressString):
        return None
    else:
        return "'%s' is not a valid email address" % newAddressString

def IMAPSaveHandler(item, fields, values):
    newAddressString = values['IMAP_EMAIL_ADDRESS']
    newFullName = values['IMAP_FULL_NAME']
    newUsername = values['IMAP_USERNAME']
    newServer = values['IMAP_SERVER']

    # If either the host or username changes, we need to set this account item
    # to inactive and create a new one.
    if (item.host and item.host != newServer) or \
       (item.username and item.username != newUsername):
        item.isActive = False
        item = Mail.IMAPAccount(view=item.itsView)

    item.replyToAddress = Mail.EmailAddress.getEmailAddress(item.itsView,
                                                            newAddressString,
                                                            newFullName)

    return item # Returning a non-None item tells the caller to continue
                # processing this item.
                # Returning None would tell the caller that processing this
                # item is complete.


def IMAPDeleteHandler(item, values, data):
    # If this IMAP account is the default, then return False to indicate it
    # can't be deleted; True otherwise.
    return not values['IMAP_DEFAULT']

def POPSaveHandler(item, fields, values):
    newAddressString = values['POP_EMAIL_ADDRESS']
    newFullName = values['POP_FULL_NAME']
    newUsername = values['POP_USERNAME']
    newServer = values['POP_SERVER']

    # If either the host or username changes, we need to set this account item
    # to inactive and create a new one.
    if (item.host and item.host != newServer) or \
       (item.username and item.username != newUsername):
        item.isActive = False
        item = Mail.POPAccount(view=item.itsView)


    item.replyToAddress = Mail.EmailAddress.getEmailAddress(item.itsView,
                                                            newAddressString,
                                                            newFullName)

    return item # Returning a non-None item tells the caller to continue
                # processing this item.
                # Returning None would tell the caller that processing this
                # item is complete.


def POPDeleteHandler(item, values, data):
    # If this POP account is the default, then return False to indicate it
    # can't be deleted; True otherwise.
    return not values['POP_DEFAULT']

def SMTPDeleteHandler(item, values, data):
    # If this SMTP account is the default for any of the IMAP accounts, return
    # False to indicate it can't be deleted; True otherwise.
    isDefault = False
    for accountData in data:
        if accountData['type'] == "IMAP":
            if accountData['values']['IMAP_SMTP'] == item.itsUUID:
                isDefault = True
                break
    return not isDefault

def WebDAVDeleteHandler(item, values, data):
    # If this WebDAV account is the default, then return False to indicate it
    # can't be deleted; True otherwise.
    return not values['WEBDAV_DEFAULT']


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
            "IMAP_SECURE" : {
                "attr" : "connectionSecurity",
                "type" : "radioEnumeration",
                "buttons" : {
                    "IMAP_SECURE_NO" : "NONE",
                    "IMAP_TLS" : "TLS",
                    "IMAP_SSL" : "SSL",
                    },
                "default" : "NONE",
                "linkedTo" : ("IMAP_PORT",
                              { "NONE":"143", "TLS":"143", "SSL":"993" } )
            },
            "IMAP_DEFAULT" : {
                "type" : "currentPointer",
                "pointer" : "currentMailAccount",
                "exclusive" : True,
            },
            "IMAP_SMTP" : {
                "type" : "itemRef",
                "attr" : "defaultSMTPAccount",
                "kind" : Mail.SMTPAccount,
            },
        },
        "id" : "IMAPPanel",
        "saveHandler" : IMAPSaveHandler,
        "validationHandler" : IMAPValidationHandler,
        "deleteHandler" : IMAPDeleteHandler,
        "displayName" : "IMAP_DESCRIPTION",
        "description" : "Incoming mail (IMAP)",
        "callbacks" : (
            ("IMAP_TEST", "OnTestIMAP"),
        )
    },
    "POP" : {
        "fields" : {
            "POP_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default": "New POP account"
            },
            "POP_EMAIL_ADDRESS" : {
                "attr" : "emailAddress",
                "type" : "string",
            },
            "POP_FULL_NAME" : {
                "attr" : "fullName",
                "type" : "string",
            },
            "POP_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "POP_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "POP_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },
            "POP_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 143,
                "required" : True,
            },
            "POP_SECURE" : {
                "attr" : "connectionSecurity",
                "type" : "radioEnumeration",
                "buttons" : {
                    "POP_SECURE_NO" : "NONE",
                    "POP_TLS" : "TLS",
                    "POP_SSL" : "SSL",
                    },
                "default" : "NONE",
                "linkedTo" : ("POP_PORT",
                              { "NONE":"110", "TLS":"110", "SSL":"995" } )
            },
            "POP_DEFAULT" : {
                "type" : "currentPointer",
                "pointer" : "currentMailAccount",
                "exclusive" : True,
            },
            "POP_SMTP" : {
                "type" : "itemRef",
                "attr" : "defaultSMTPAccount",
                "kind" : Mail.SMTPAccount,
            },
            "POP_LEAVE" : {
                "attr" : "leaveOnServer",
                "type" : "boolean",
            },
        },
        "id" : "POPPanel",
        "saveHandler" : POPSaveHandler,
        "deleteHandler" : POPDeleteHandler,
        "displayName" : "POP_DESCRIPTION",
        "description" : "Incoming mail (POP)",
        "callbacks" : (
            ("POP_TEST", "OnTestPOP"),
        )
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
            "SMTP_SECURE" : {
                "attr" : "connectionSecurity",
                "type" : "radioEnumeration",
                "buttons" : {
                    "SMTP_SECURE_NO" : "NONE",
                    "SMTP_SECURE_TLS" : "TLS",
                    "SMTP_SECURE_SSL" : "SSL",
                    },
                "default" : "NONE",
                "linkedTo" : ("SMTP_PORT",
                              { "NONE":"25", "TLS":"25", "SSL":"465" } )
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
        "deleteHandler" : SMTPDeleteHandler,
        "displayName" : "SMTP_DESCRIPTION",
        "description" : "Outgoing mail (SMTP)",
        "callbacks" : (
            ("SMTP_TEST", "OnTestSMTP"),
        )
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
                "pointer" : "currentWebDAVAccount",
                "exclusive" : True,
            },
        },
        "id" : "WebDAVPanel",
        "deleteHandler" : WebDAVDeleteHandler,
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

        # Load the various account form panels:
        self.panels = {}
        for (key, value) in PANELS.iteritems():
            self.panels[key] = self.resources.LoadPanel(self, value['id'])
            self.panels[key].Hide()

        self.SetSizer(self.outerSizer)
        self.outerSizer.SetSizeHints(self)
        self.outerSizer.Fit(self)

        self.accountsList = wx.xrc.XRCCTRL(self, "ACCOUNTS_LIST")
        self.choiceNewType = wx.xrc.XRCCTRL(self, "CHOICE_NEW_ACCOUNT")

        # Populate the "new account" listbox:
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

        # If the user deletes an account, its data will be moved here:
        self.deletions = [ ]

        self.__PopulateAccountsList(account)

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
        """ Find all account items and put them in the list; also build
            up a data structure with the applicable attribute values we'll
            be editing. If account is passed in, show its details. """

        # Make sure we're sync'ed with any changes other threads have made
        self.view.refresh()
        accountIndex = 0 # which account to select first
        accounts = []

        for cls in (Mail.IMAPAccount, Mail.POPAccount, Mail.SMTPAccount):
            for item in cls.iterItems(self.view):
                if item.isActive and hasattr(item, 'displayName'):
                    accounts.append(item)

        for item in Sharing.WebDAVAccount.iterItems(self.view):
            if hasattr(item, 'displayName'):
                accounts.append(item)

        i = 0

        for item in accounts:

            # If an account was passed in, remember its index so we can
            # select it
            if account == item:
                accountIndex = i

            # 'values' is a dict whose keys are the field names defined in
            # the PANELS data structure above
            values = { }

            for (field, desc) in \
             PANELS[item.accountType]['fields'].iteritems():

                if desc['type'] == 'currentPointer':
                    # See if this item is the current item for the given
                    # pointer name, storing a boolean.
                    app = schema.ns('osaf.app', self.view)
                    ref = getattr(app, desc['pointer'])
                    setting = (ref.item == item)

                elif desc['type'] == 'itemRef':
                    # Store an itemRef as a UUID
                    try:
                        setting = item.getAttributeValue(desc['attr']).itsUUID
                    except:
                        setting = None

                else:
                    # Otherwise store a literal
                    try:
                        setting = item.getAttributeValue(desc['attr'])
                    except AttributeError:
                        try:
                            setting = desc['default']
                        except KeyError:
                            setting = DEFAULTS[desc['type']]

                values[field] = setting

            # Store a dictionary for this account, including the following:
            self.data.append( { "item"   : item.itsUUID,
                                "values" : values,
                                "type"   : item.accountType,
                                "isNew"  : False } )

            self.accountsList.Append(item.displayName)

            i += 1
            # End of account loop

        if i > 0:
            self.accountsList.SetSelection(accountIndex)
            self.__SwapDetailPanel(accountIndex)


    def __ApplyChanges(self):
        """ Take the data from the list and apply the values to the items. """

        # First store the current form values to the data structure
        self.__StoreFormData(self.currentPanelType,
                             self.currentPanel,
                             self.data[self.currentIndex]['values'])

        for account in self.data:

            uuid = account['item']

            if uuid:
                # We already have an account item created
                item = self.view.findUUID(account['item'])

            else:
                # We need to create an account item

                if account['type'] == "IMAP":
                    item = Mail.IMAPAccount(view=self.view)

                elif account['type'] == "POP":
                    item = Mail.POPAccount(view=self.view)

                elif account['type'] == "SMTP":
                    item = Mail.SMTPAccount(view=self.view)

                    #XXX: Temp change that checks if no SMTP Account currently
                    #     exists and makes the new account the defaultSMTPAccount
                    #     for the default IMAP ccount

                    if Mail.getCurrentSMTPAccount(view=self.view)[0] is None:
                        mailAccount = Mail.getCurrentMailAccount(view=self.view)

                        if mailAccount is not None:
                            mailAccount.defaultSMTPAccount = item

                elif account['type'] == "WebDAV":
                    item = Sharing.WebDAVAccount(view=self.view)

            values = account['values']
            panel = PANELS[account['type']]

            if panel.has_key("saveHandler"):
                # Call custom save handler; if None returned, we don't do
                # any more processing of that account within this loop
                item = panel["saveHandler"](item, panel['fields'], values)

            if item is not None:
                # Process each field defined in the PANEL data structure;
                # applying the values to the appropriate attributes:

                for (field, desc) in panel['fields'].iteritems():

                    if desc['type'] == 'currentPointer':
                        # If this value is True, make this item current:
                        if values[field]:
                            app = schema.ns('osaf.app', self.view)
                            ref = getattr(app, desc['pointer'])
                            ref.item = item

                    elif desc['type'] == 'itemRef':
                        # Find the item for this UUID and assign the itemref:
                        if values[field]:
                            item.setAttributeValue(desc['attr'],
                                self.view.findUUID(values[field]))

                    else:
                        # Otherwise, make the literal assignment:
                        try:
                            item.setAttributeValue(desc['attr'], values[field])
                        except:
                            pass


    def __ApplyDeletions(self):
        # Since we don't delete items right away, we need to do it here:

        for data in self.deletions:
            uuid = data['item']
            if uuid:
                item = self.view.findUUID(uuid)
                item.delete()

    def __ApplyCancellations(self):
        # The only thing we need to do on Cancel is to remove any account items
        # we created this session:

        for accountData in self.data:
            if accountData['isNew']:
                uuid = accountData['item']
                item = self.view.findUUID(uuid)
                item.delete()


    def __Validate(self):
        # Call any custom validation handlers that might be defined

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

                invalidMessage = panel["validationHandler"](item,
                    panel['fields'], values)

                if invalidMessage:
                    # Show the invalid panel
                    self.accountsList.SetSelection(i)
                    self.__SwapDetailPanel(i)
                    application.dialogs.Util.ok(self, "Invalid Entry",
                                                invalidMessage)
                    return False

            i += 1

        return True


    def __GetDisplayName(self, index):
        # Each panel type has a field that is designated the displayName; this
        # method determines which field is the displayName, then gets the value

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

            # This enables the clicking of a radio button to affect the value
            # of another field.  In this case, the OnLinkedControl( ) method
            # will get called.
            if fieldInfo['type'] == "radioEnumeration":
                linkedTo = fieldInfo.get('linkedTo', None)
                if linkedTo is not None:
                    for (button, value) in fieldInfo['buttons'].iteritems():
                        control = wx.xrc.XRCCTRL(self.currentPanel, button)
                        wx.EVT_RADIOBUTTON(control, control.GetId(),
                                           self.OnLinkedControl)
                continue

            control = wx.xrc.XRCCTRL(self.currentPanel, field)

            if isinstance(control, wx.TextCtrl):
                wx.EVT_SET_FOCUS(control, self.OnFocusGained)

            elif isinstance(control, wx.RadioButton):
                # Set up the callback for an "exclusive" radio button, i.e.,
                # one who when checked within one account will get unchecked
                # in all other accounts
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
                    wx.EVT_RADIOBUTTON(control,
                                       control.GetId(),
                                       self.OnExclusiveRadioButton)

            elif isinstance(control, wx.CheckBox):
                # This allows a checkbox to affect the value of another field
                linkedTo = fieldInfo.get('linkedTo', None)
                if linkedTo is not None:
                    wx.EVT_CHECKBOX(control,
                                    control.GetId(),
                                    self.OnLinkedControl)

        # Hook up any other callbacks not tied to any fields, such as the
        # account testing buttons:
        for callbackReg in PANELS[self.currentPanelType].get('callbacks', ()):
            self.Bind(wx.EVT_BUTTON,
                      getattr(self, callbackReg[1]),
                      id=wx.xrc.XRCID(callbackReg[0]))


    def __StoreFormData(self, panelType, panel, data):
        # Store data from the wx widgets into the "data" dictionary

        for field in PANELS[panelType]['fields'].keys():

            fieldInfo = PANELS[panelType]['fields'][field]
            valueType = fieldInfo['type']
            valueRequired = fieldInfo.get('required', False)

            if fieldInfo['type'] == 'radioEnumeration':
                # A radio button group is handled differently, since there
                # are multiple wx controls controlling a single attribute.
                for (button, value) in fieldInfo['buttons'].iteritems():
                    control = wx.xrc.XRCCTRL(panel, button)
                    if control.GetValue() == True:
                        data[field] = value
                        break
                continue

            control = wx.xrc.XRCCTRL(panel, field)

            # Handle strings:
            if valueType == "string":
                val = control.GetValue().strip()
                if valueRequired and not val:
                    continue

            # Handle booleans:
            elif valueType == "boolean":
                val = (control.GetValue() == True)

            # Handle current pointers, which are stored as booleans:
            elif valueType == "currentPointer":
                val = (control.GetValue() == True)

            # Handle itemrefs, which are stored as UUIDs:
            elif valueType == "itemRef":
                index = control.GetSelection()
                if index == -1:
                    val = None
                else:
                    val = control.GetClientData(index)

            # Handle integers:
            elif valueType == "integer":
                try:
                    val = int(control.GetValue().strip())
                except:
                    # Skip if not valid
                    continue

            data[field] = val


    def __FetchFormData(self, panelType, panel, data):
        # Pull data out of the "data" dictionary and stick it into the widgets:

        for field in PANELS[panelType]['fields'].keys():

            fieldInfo = PANELS[panelType]['fields'][field]

            if fieldInfo['type'] == 'radioEnumeration':
                # a radio button group is handled differently, since there
                # are multiple wx controls controlling a single attribute.
                for (button, value) in fieldInfo['buttons'].iteritems():
                    if value == data[field]:
                        control = wx.xrc.XRCCTRL(panel, button)
                        control.SetValue(True)
                        break
                continue

            control = wx.xrc.XRCCTRL(panel, field)

            valueType = PANELS[panelType]['fields'][field]['type']

            # Handle strings:
            if valueType == "string":
                control.SetValue(data[field])

            # Handle booleans:
            elif valueType == "boolean":
                control.SetValue(data[field])

            # Handle current pointers, which are stored as booleans:
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

            # Handle itemrefs, which are stored as UUIDs.  We need to find
            # all items of the kind specified in the PANEL, filtering out those
            # which have been marked for deletion, or are inactive.
            elif valueType == "itemRef":
                items = []
                count = 0
                index = -1
                uuid = data[field]
                kindClass = PANELS[panelType]['fields'][field]['kind']
                for item in kindClass.iterItems(self.view):
                    deleted = False
                    for accountData in self.deletions:
                        if accountData['item'] == item.itsUUID:
                            deleted = True
                            break

                    if item.isActive and not deleted:
                        items.append(item)
                        if item.itsUUID == uuid:
                            index = count
                        count += 1

                control.Clear()

                for item in items:
                    # Add items to the dropdown list...

                    # ...however we need to grab displayName from the form
                    # data rather than from the item (as long as it's an item
                    # that's being edited in the dialog).  If the item doesn't
                    # appear in self.data, then it's an item that isn't being
                    # edited by the dialog and therefore we can ask it directly
                    # for its displayName:

                    displayName = item.displayName
                    for accountData in self.data:
                        if item.itsUUID == accountData['item']:
                            displayNameField = \
                                PANELS[item.accountType]['displayName']
                            displayName = \
                                accountData['values'][displayNameField]
                            break

                    newIndex = control.Append(displayName)
                    control.SetClientData(newIndex, item.itsUUID)

                if index != -1:
                    control.SetSelection(index)

            # Handle integers:
            elif valueType == "integer":
                control.SetValue(str(data[field]))


    def OnOk(self, evt):
        if self.__Validate():
            self.__ApplyChanges()
            self.__ApplyDeletions()
            self.EndModal(True)
            self.view.commit()
            application.Globals.mailService.refreshMailServiceCache()
            self.Destroy()

    def OnCancel(self, evt):
        self.__ApplyCancellations()
        self.EndModal(False)
        self.Destroy()

    def OnNewAccount(self, evt):

        selection = self.choiceNewType.GetSelection()
        if selection == 0:
            return

        accountType = self.choiceNewType.GetClientData(selection)
        self.choiceNewType.SetSelection(0)

        if accountType == "IMAP":
            item = Mail.IMAPAccount(view=self.view)
        elif accountType == "POP":
            item = Mail.POPAccount(view=self.view)
        elif accountType == "SMTP":
            item = Mail.SMTPAccount(view=self.view)
        elif accountType == "WebDAV":
            item = Sharing.WebDAVAccount(view=self.view)

        accountName = "New %s account" % accountType
        item.displayName = accountName

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

        self.data.append( { "item" : item.itsUUID,
                            "values" : values,
                            "type" : accountType,
                            "isNew" : True } )

        index = self.accountsList.Append(accountName)
        self.accountsList.SetSelection(index)
        self.__SwapDetailPanel(index)


    def OnDeleteAccount(self, evt):
        # First, make sure any values that have been modified in the form
        # are stored:
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        index = self.accountsList.GetSelection()
        item = self.view.findUUID(self.data[index]['item'])
        deleteHandler = PANELS[item.accountType]['deleteHandler']
        canDelete = deleteHandler(item, self.data[index]['values'], self.data)
        if canDelete:
            self.accountsList.Delete(index)
            self.deletions.append(self.data[index])
            del self.data[index]
            self.innerSizer.Detach(self.currentPanel)
            self.currentPanel.Hide()
            self.currentIndex = None
            self.accountsList.SetSelection(0)
            self.__SwapDetailPanel(0)
        else:
            msg = "This account currently may not be deleted because it has been marked as a 'default' account"
            application.dialogs.Util.ok(self, "Cannot delete default account",
                                        msg)


    def OnTestIMAP(self, evt):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        account = schema.ns('osaf.app', self.view).TestIMAPAccount
        account.host = data['IMAP_SERVER']
        account.port = data['IMAP_PORT']
        account.connectionSecurity = data['IMAP_SECURE']
        account.username = data['IMAP_USERNAME']
        account.password = data['IMAP_PASSWORD']

        self.view.commit()
        application.Globals.mailService.getIMAPInstance(account).testAccountSettings()

    def OnTestSMTP(self, evt):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        uuid = self.data[self.currentIndex]['item']
        data = self.data[self.currentIndex]['values']

        account = schema.ns('osaf.app', self.view).TestSMTPAccount
        account.host = data['SMTP_SERVER']
        account.port = data['SMTP_PORT']
        account.connectionSecurity = data['SMTP_SECURE']
        account.useAuth = data['SMTP_USE_AUTH']
        account.username = data['SMTP_USERNAME']
        account.password = data['SMTP_PASSWORD']

        self.view.commit()
        application.Globals.mailService.getSMTPInstance(account).testAccountSettings()

    def OnTestPOP(self, evt):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        account = schema.ns('osaf.app', self.view).TestPOPAccount
        account.host = data['POP_SERVER']
        account.port = data['POP_PORT']
        account.connectionSecurity = data['POP_SECURE']
        account.leaveOnServer = data['POP_LEAVE']
        account.username = data['POP_USERNAME']
        account.password = data['POP_PASSWORD']

        self.view.commit()
        application.Globals.mailService.getPOPInstance(account).testAccountSettings()


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
                                    path=path, repositoryView=self.view)
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
        elif result == WebDAV.IGNORE:
            # Leave msg as None to ignore it
            msg = None
        else:
            # This shouldn't happen
            msg = "Test failed with an unknown response."

        if msg is not None:
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
        # A "linked" control has been clicked -- we need to modify the value
        # of the field this is linked to, but only if that field is already
        # set to one of the predefined values.

        control = evt.GetEventObject()

        # Determine current panel
        panel = PANELS[self.currentPanelType]

        # Scan through fields, seeing if this control corresponds to one
        # If marked as linkedTo, change the linked field
        ##        "linkedTo" : ("IMAP_PORT", { True:993, False:143 } )
        for (field, fieldInfo) in panel['fields'].iteritems():

            ids = []
            if fieldInfo['type'] == 'radioEnumeration':
                for (button, fieldValue) in fieldInfo['buttons'].iteritems():
                    buttonId = wx.xrc.XmlResource.GetXRCID(button)
                    ids.append(buttonId)
                    if buttonId == control.GetId():
                        value = fieldValue
            else:
                ids = [wx.xrc.XmlResource.GetXRCID(field)]
                value = control.GetValue()

            if control.GetId() in ids:
                linkedTo = fieldInfo.get('linkedTo', None)
                if linkedTo is not None:
                    linkedField = linkedTo[0]
                    linkedValues = linkedTo[1]
                    linkedControl = wx.xrc.XRCCTRL(self.currentPanel,
                                                   linkedField)
                    if linkedControl.GetValue() in (linkedValues.values()):
                        linkedControl.SetValue(linkedValues[value])
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
                # This control matches

                # Double check it is an exclusive:
                if fieldInfo.get('exclusive', False):

                    # Set all other accounts sharing this current pointer to
                    # False:

                    index = 0
                    for accountData in self.data:

                        # Skip the current account
                        if index != self.currentIndex:

                            aPanel = PANELS[accountData['type']]
                            for (aField, aFieldInfo) in \
                                aPanel['fields'].iteritems():
                                if aFieldInfo.get('type') == 'currentPointer':
                                    if aFieldInfo.get('pointer', '') == \
                                        fieldInfo.get('pointer'):
                                            accountData['values'][aField] = \
                                                False
                        index += 1
                    break


def ShowAccountPreferencesDialog(parent, account=None, view=None, modal=True):

    # Parse the XRC resource file:
    xrcFile = os.path.join(application.Globals.chandlerDirectory,
     'application', 'dialogs', 'AccountPreferences_wdr.xrc')
    resources = wx.xrc.XmlResource(xrcFile)

    # Display the dialog:
    win = AccountPreferencesDialog(parent, "Account Preferences",
     resources=resources, account=account, view=view)
    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
