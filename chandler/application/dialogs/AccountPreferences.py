import os
import wx
import wx.xrc
import application.Globals
from application.Globals import repository as repo
from application.Globals import parcelManager as pm
from repository.item.Query import KindQuery

# Used to lookup the mail model parcel:
MAIL_MODEL = "http://osafoundation.org/parcels/osaf/contentmodel/mail"
# Used to lookup the webdav parcel:
WEBDAV_MODEL = "http://osafoundation.org/parcels/osaf/framework/webdav"

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
        "id" : "IMAPPane",
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
        "id" : "SMTPPane",
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
            },
            "WEBDAV_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
            },
        },
        "id" : "WebDAVPane",
    },
}

class AccountPreferencesDialog(wx.Dialog):
    def __init__(self, parent, resources):
        pre = wx.PreDialog()
        self.resources = resources
        resources.LoadOnDialog(pre, parent, 'AccountPrefsDialog')
        self.this = pre.this

        self.accountsList = wx.xrc.XRCCTRL(self, "ACCOUNTS_LIST")
        self.detailsPanel = wx.xrc.XRCCTRL(self, "DETAILS_PANEL")
        self.currentIndex = None # the list index of account in detail panel
        self.currentPanelType = None
        self.data = [ ]

        wx.EVT_BUTTON( self, wx.xrc.XRCID( "OK_BUTTON" ), self.OnOk )
        wx.EVT_BUTTON( self, wx.xrc.XRCID( "CANCEL_BUTTON" ), self.OnCancel )
        wx.EVT_LISTBOX( self, wx.xrc.XRCID( "ACCOUNTS_LIST" ),
         self.OnAccountSel )

        self.__PopulateAccountsList()

    def __PopulateAccountsList(self):
        """ Find all AccountBase items and put them in the list; also build
            up a data structure with the applicable attribute values we'll
            be editing. """

        # Make sure we're sync'ed with any changes other threads have made
        repo.commit()

        accountKind = pm.lookup(MAIL_MODEL, "AccountBase")
        webDavAccountKind = pm.lookup(WEBDAV_MODEL, "WebDAVAccount")
        i = 0
        for item in KindQuery().run([accountKind, webDavAccountKind]):
            values = { }
            for (field, desc) in \
             PANELS[item.accountType]['fields'].iteritems():
                values[field] = item.getAttributeValue(desc['attr'])
            self.data.append( { "item" : item, "values" : values } )
            self.accountsList.Append(item.displayName)
            i += 1

        if i > 0:
            self.accountsList.SetSelection(0)
            self.__SwapDetailPane(0)


    def __ApplyChanges(self):
        """ Take the data from the list and apply the values to the items. """

        # First store the current form values to the data structure
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        for account in self.data:
            item = account['item']
            values = account['values']
            for (field, desc) in \
             PANELS[item.accountType]['fields'].iteritems():
                item.setAttributeValue(desc['attr'], values[field])

        repo.commit()

    def __SwapDetailPane(self, index):
        """ Given an index into the account list, store the current pane's
            (if any) contents to the data list, destroy current pane, determine
            type of pane to pull in, load it, populated it. """

        if self.currentIndex != None:
            # Get current form data and tuck it away
            self.__StoreFormData(self.currentPanelType, self.currentPanel,
             self.data[self.currentIndex]['values'])
            self.detailsPanel.DestroyChildren()

        self.currentIndex = index
        self.currentPanelType = self.data[index]['item'].accountType
        self.currentPanel = self.resources.LoadPanel(self.detailsPanel,
         PANELS[self.currentPanelType]['id'])
        self.__FetchFormData(self.currentPanelType, self.currentPanel,
         self.data[index]['values'])

    def __StoreFormData(self, panelType, panel, data):
        for field in PANELS[panelType]['fields'].keys():
            control = wx.xrc.XRCCTRL(panel, field)
            valueType = PANELS[panelType]['fields'][field]['type']
            if valueType == "string":
                val = control.GetValue()
            elif valueType == "boolean":
                val = (control.GetValue() == True)
            elif valueType == "integer":
                val = int(control.GetValue())
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
        self.__ApplyChanges()
        self.EndModal(True)

    def OnCancel(self, evt):
        self.EndModal(False)

    def OnAccountSel(self, evt):
        # Huh? This is always False!
        # if not evt.IsSelection(): return

        sel = evt.GetSelection()
        self.__SwapDetailPane(sel)

def ShowAccountPreferencesDialog(parent):
        xrcFile = os.path.join(application.Globals.chandlerDirectory,
         'application', 'dialogs', 'AccountPreferences_wdr.xrc')
        resources = wx.xrc.XmlResource(xrcFile)
        win = AccountPreferencesDialog(parent, resources)
        win.CenterOnScreen()
        val = win.ShowModal()
        win.Destroy()
