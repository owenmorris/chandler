import os
import wx
import wx.xrc
import application.Globals
from repository.item.Query import KindQuery
import osaf.contentmodel.mail.Mail as Mail
import application.dialogs.Util

# Used to lookup the mail model parcel:
MAIL_MODEL = "http://osafoundation.org/parcels/osaf/contentmodel/mail"
# Used to lookup the webdav parcel:
WEBDAV_MODEL = "http://osafoundation.org/parcels/osaf/framework/webdav"

# Special handlers referenced in the PANELS dictionary below:

def IMAPValidationHandler(item, fields, values):
    """ Return False if any invalid fields, True otherwise """
    if not Mail.EmailAddress.isValidEmailAddress(values['IMAP_EMAIL_ADDRESS']):
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
         "Invalid Email Address", "The email address, '%s', is invalid" % \
         (values['IMAP_EMAIL_ADDRESS']))
        return False
    return True

def IMAPSaveHandler(item, fields, values):
    newAddressString = values['IMAP_EMAIL_ADDRESS']
    newFullName = values['IMAP_FULL_NAME']

    # If there isn't already an emailAddress set up, just reuse the empty
    # default EmailAddress item.  Otherwise, possibly fetch a new EmailAddress
    # item.
    if item.replyToAddress.emailAddress:
        # Use the getEmailAddress( ) factory method to retrieve the appropriate
        # EmailAddress item (could be an existing one if the fields match, or
        # a new one could be created)
        item.replyToAddress = \
         Mail.EmailAddress.getEmailAddress(item.itsView, newAddressString,
         newFullName)
        if item.replyToAddress is None:
            print "Error, got None from getEmailAddress(%s, %s)" % \
             (newAddressString, newFullName)

    # process as normal:
    for (field, desc) in fields.iteritems():
        item.setAttributeValue(desc['attr'], values[field])

# Used to map form fields to item attributes:
PANELS = {
    "IMAP" : {
        "fields" : {
            "IMAP_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
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
            },
            "IMAP_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
            },
        },
        "id" : "IMAPPanel",
        "saveHandler" : IMAPSaveHandler,
        "validationHandler" : IMAPValidationHandler,
    },
    "SMTP" : {
        "fields" : {
            "SMTP_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
            },
            "SMTP_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "SMTP_PORT" : {
                "attr" : "port",
                "type" : "integer",
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
    },
    "WebDAV" : {
        "fields" : {
            "WEBDAV_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
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
                "default": 80
            },
            "WEBDAV_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
            },
        },
        "id" : "WebDAVPanel",
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
        self.currentIndex = None # the list index of account in detail panel
        self.currentPanelType = None
        self.currentPanel = None # whatever detail panel we swap in

        # data is a list of dictionaries of the form:
        # 'item' => item.itsUUID
        # 'values' => a dict mapping field names to attribute values
        # The order of the data list needs to be the same order as what's in
        # the accounts list widget.
        self.data = [ ]

        self.__PopulateAccountsList(account)

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

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
        imapAccountKind = application.Globals.parcelManager.lookup(MAIL_MODEL, "IMAPAccount")
        smtpAccountKind = application.Globals.parcelManager.lookup(MAIL_MODEL, "SMTPAccount")
        webDavAccountKind = application.Globals.parcelManager.lookup(WEBDAV_MODEL, "WebDAVAccount")

        accounts = []

        imapAccount = None
        for item in KindQuery().run([imapAccountKind]):
            imapAccount = item
            if item.isDefault:
                break
        accounts.append(imapAccount)

        smtpAccount = None
        for item in KindQuery().run([smtpAccountKind]):
            smtpAccount = item
            if item.isDefault:
                break
        accounts.append(smtpAccount)

        webdavAccount = None
        for item in KindQuery().run([webDavAccountKind]):
            webdavAccount = item
            if item.isDefault:
                break
        accounts.append(webdavAccount)

        i = 0
        for item in accounts:
            if account == item:
                accountIndex = i
            values = { }
            for (field, desc) in \
             PANELS[item.accountType]['fields'].iteritems():
                try:
                    setting = item.getAttributeValue(desc['attr'])
                except AttributeError:
                    try:
                        setting = desc['default']
                    except KeyError:
                        setting = DEFAULTS[desc['type']]
                values[field] = setting
            self.data.append( { "item" : item.itsUUID, "values" : values } )
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
            item = self.view.findUUID(account['item'])
            values = account['values']
            panel = PANELS[item.accountType]
            if panel.has_key("saveHandler"):
                panel["saveHandler"](item, panel['fields'], values)
            else:
                for (field, desc) in \
                 panel['fields'].iteritems():
                    item.setAttributeValue(desc['attr'], values[field])

    def __Validate(self):

        # First store the current form values to the data structure
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        i = 0
        for account in self.data:
            item = self.view.findUUID(account['item'])
            values = account['values']
            panel = PANELS[item.accountType]
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

    def __SwapDetailPanel(self, index):
        """ Given an index into the account list, store the current panel's
            (if any) contents to the data list, destroy current panel, determine
            type of panel to pull in, load it, populated it. """

        if index == self.currentIndex: return

        if self.currentIndex != None:
            # Get current form data and tuck it away
            self.__StoreFormData(self.currentPanelType, self.currentPanel,
             self.data[self.currentIndex]['values'])
            self.innerSizer.Detach(self.currentPanel)
            self.currentPanel.Hide()

        self.currentIndex = index
        item = self.view.findUUID(self.data[index]['item'])
        self.currentPanelType = item.accountType
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
        for field in PANELS[self.currentPanelType]['fields'].keys():
            control = wx.xrc.XRCCTRL(self.currentPanel, field)
            if isinstance(control, wx.TextCtrl):
                wx.EVT_SET_FOCUS(control, self.OnFocusGained)



    def __StoreFormData(self, panelType, panel, data):
        for field in PANELS[panelType]['fields'].keys():
            control = wx.xrc.XRCCTRL(panel, field)
            valueType = PANELS[panelType]['fields'][field]['type']
            if valueType == "string":
                val = control.GetValue().strip()
            elif valueType == "boolean":
                val = (control.GetValue() == True)
            elif valueType == "integer":
                val = int(control.GetValue().strip())
            data[field] = val

    def __FetchFormData(self, panelType, panel, data):
        for field in PANELS[panelType]['fields'].keys():
            control = wx.xrc.XRCCTRL(panel, field)
            valueType = PANELS[panelType]['fields'][field]['type']
            if valueType == "string":
                control.SetValue(data[field])
            elif valueType == "boolean":
                control.SetValue(data[field])
            elif valueType == "integer":
                control.SetValue(str(data[field]))

    def OnOk(self, evt):
        if self.__Validate():
            self.__ApplyChanges()
            self.EndModal(True)
            self.view.commit()

    def OnCancel(self, evt):
        self.EndModal(False)

    def OnAccountSel(self, evt):
        # Huh? This is always False!
        # if not evt.IsSelection(): return

        sel = evt.GetSelection()
        self.__SwapDetailPanel(sel)

    def OnFocusGained(self, evt):
        """ Select entire text field contents when focus is gained. """
        control = evt.GetEventObject()
        wx.CallAfter(control.SetSelection, -1, -1)


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
