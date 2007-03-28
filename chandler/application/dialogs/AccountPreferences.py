# Copyright (c) 2003-2006 Open Source Applications FoundationA411
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


# Account Preferences Dialog
# Invoke this using the ShowAccountPreferencesDialog() method

import os, sys
import wx
import wx.xrc

import application.schema as schema
from   application import Globals, Utility
import application.Parcel
from application.dialogs import Util
import osaf.pim.mail as Mail
from osaf.mail import constants
from osaf import sharing
from i18n import ChandlerMessageFactory as _
from osaf.framework.blocks.Block import Block
from AccountPreferencesDialogs import MailTestDialog, \
                                      AutoDiscoveryDialog, \
                                      ChandlerIMAPFoldersDialog, \
                                      RemoveChandlerIMAPFoldersDialog, \
                                      SharingTestDialog, \
                                      showYesNoDialog, \
                                      showOKDialog, \
                                      showConfigureDialog


# Localized messages displayed in dialogs

CREATE_TEXT = _(u"Configure")
REMOVE_TEXT = _(u"Remove")

# --- Error Messages ----- #
FIELDS_REQUIRED = _(u"The following fields are required:\n\n\tServer\n\tUser name\n\tPassword\n\tPort\n\n\nPlease correct the error and try again.")
FIELDS_REQUIRED_ONE = _(u"The following fields are required:\n\n\tServer\n\tPort\n\n\nPlease correct the error and try again.")
FIELDS_REQUIRED_TWO = _(u"The following fields are required:\n\n\tServer\n\tPath\n\tUser name\n\tPassword\n\tPort\n\n\nPlease correct the error and try again.")

HOST_REQUIRED  = _(u"Auto-configure requires a server name.")




# --- Yes No Dialog Messages ----- #
CREATE_FOLDERS_TITLE = _(u"Configure Chandler folders")
CREATE_FOLDERS = _(u"Chandler will now attempt to create the following IMAP folders in your account\non '%(host)s':\n\n\tChandler Mail\n\tChander Tasks\n\tChandler Events\n\nIf you have already set up Chandler folders in your account, no new folders\nwill be created.")

REMOVE_FOLDERS_TITLE = _(u"Remove Chandler folders")
REMOVE_FOLDERS = _(u"Chandler will now attempt to remove the\nfollowing IMAP folders on '%(host)s':\n\n\tChandler Mail\n\tChander Tasks\n\tChandler Events\n\n Would you like to proceed?")


# Will print out saved account changes
# before exiting the dialog when set to True
DEBUG = False
FOLDERS_URL = "http://wiki.osafoundation.org/Projects/ChandlerProductFAQ"
SHARING_URL = "https://osaf.us/account/new"

# Special handlers referenced in the PANELS dictionary below:

def IncomingValidationHandler(item, fields, values):
    newAddressString = values['INCOMING_EMAIL_ADDRESS']
    # Blank address string?  Don't bother the user now, they will get
    # reminded when they actually try to fetch mail.  Bogus address?
    # They better fix it before leaving the dialog box.
    if not newAddressString or \
        Mail.EmailAddress.isValidEmailAddress(newAddressString):
        return None
    else:
        return _(u"'%(emailAddress)s' is not a valid email address") % \
                {'emailAddress': newAddressString}

def IncomingSaveHandler(item, fields, values):
    newAddressString = values['INCOMING_EMAIL_ADDRESS']
    newFullName = values['INCOMING_FULL_NAME']
    newUsername = values['INCOMING_USERNAME']
    newServer = values['INCOMING_SERVER']
    newAccountProtocol = values['INCOMING_PROTOCOL']

    # If either the host, username, or protocol changes
    # we need to set this account item to inactive and
    # create a new one.
    if (item.host and item.host != newServer) or \
       (item.username and item.username != newUsername) or \
       (item.accountProtocol != newAccountProtocol):
        item.isActive = False

        ns_pim = schema.ns('osaf.pim', item.itsView)

        isCurrent = item == ns_pim.currentIncomingAccount.item
        oldItem   = item

        if newAccountProtocol == "IMAP":
            item = Mail.IMAPAccount(itsView=item.itsView)

        elif newAccountProtocol == "POP":
            item = Mail.POPAccount(itsView=item.itsView)
        else:
            # If this code is reached then there is a
            # bug which needs to be fixed.
            raise Exception("Internal Exception")

        if isCurrent:
            ns_pim.currentIncomingAccount.item = item


    item.replyToAddress = Mail.EmailAddress.getEmailAddress(item.itsView,
                                                            newAddressString,
                                                            newFullName)


    return item # Returning a non-None item tells the caller to continue
                # processing this item.
                # Returning None would tell the caller that processing this
                # item is complete.


def IncomingDeleteHandler(item, values, data):
    ns_pim = schema.ns('osaf.pim', item.itsView)
    return not item == ns_pim.currentIncomingAccount.item

def OutgoingSaveHandler(item, fields, values):
    newAddressString = values['OUTGOING_FROM']
    newFullName = ""


    item.fromAddress = Mail.EmailAddress.getEmailAddress(item.itsView,
                                                         newAddressString,
                                                         newFullName)

    return item # Returning a non-None item tells the caller to continue
                # processing this item.
                # Returning None would tell the caller that processing this
                # item is complete.

def OutgoingDeleteHandler(item, values, data):
    ns_pim = schema.ns('osaf.pim', item.itsView)
    return not item == ns_pim.currentOutgoingAccount.item

def SharingDeleteHandler(item, values, data):
    sharing_ns = schema.ns('osaf.sharing', item.itsView)
    return not item == sharing_ns.currentSharingAccount.item

# Used to map form fields to item attributes:
PANELS = {
    "INCOMING" : {
        "fields" : {
            "INCOMING_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default": _(u"New Incoming Mail Account"),
            },
            "INCOMING_EMAIL_ADDRESS" : {
                "attr" : "emailAddress",
                "type" : "string",
            },
            "INCOMING_FULL_NAME" : {
                "attr" : "fullName",
                "type" : "string",
            },
            "INCOMING_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "INCOMING_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "INCOMING_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },

            "INCOMING_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 143,
                "required" : True,
            },

            "INCOMING_PROTOCOL" : {
                "attr" : "accountProtocol",
                "type" : "choice",
                "default": "IMAP",
            },

            "INCOMING_SECURE" : {
                "attr" : "connectionSecurity",
                "type" : "radioEnumeration",
                "buttons" : {
                    "INCOMING_SECURE_NO" : "NONE",
                    "INCOMING_TLS" : "TLS",
                    "INCOMING_SSL" : "SSL",
                    },
                "default" : "NONE",
                "linkedTo" :
                 {
                   "callback": "getIncomingProtocol",
                   "protocols": {
                      "IMAP": ("INCOMING_PORT", { "NONE":"143", "TLS":"143", "SSL":"993" } ),
                      "POP":  ("INCOMING_PORT", { "NONE":"110", "TLS":"110", "SSL":"995" } ),
                    },
                 }
            },

            "INCOMING_FOLDERS" : {
                "attr" : "folders",
                "type" : "chandlerFolders",
            },
        },
        "id" : "INCOMINGPanel",
        "saveHandler" : IncomingSaveHandler,
        "validationHandler" : IncomingValidationHandler,
        "deleteHandler" : IncomingDeleteHandler,
        "displayName" : u"INCOMING_DESCRIPTION",
        "description" : _(u"Incoming mail"),
        "callbacks" : (
                        ("INCOMING_DISCOVERY", "OnIncomingDiscovery"),
                      ),
        "messages" : ("INCOMING_MESSAGE",),
        "init" : "initIncomingPanel",
    },
    "OUTGOING" : {
        "fields" : {
            "OUTGOING_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default": _(u"New Outgoing Mail Account"),
            },
            "OUTGOING_FROM" : {
                "attr" : "emailAddress",
                "type" : "string",
            },
            "OUTGOING_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "OUTGOING_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 25,
                "required" : True,
            },
            "OUTGOING_SECURE" : {
                "attr" : "connectionSecurity",
                "type" : "radioEnumeration",
                "buttons" : {
                    "OUTGOING_SECURE_NO" : "NONE",
                    "OUTGOING_SECURE_TLS" : "TLS",
                    "OUTGOING_SECURE_SSL" : "SSL",
                    },
                "default" : "NONE",
                "linkedTo" :
                        ("OUTGOING_PORT", { "NONE":"25", "TLS":"25", "SSL":"465" }),
            },
            "OUTGOING_USE_AUTH" : {
                "attr" : "useAuth",
                "type" : "boolean",
            },
            "OUTGOING_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "OUTGOING_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },
        },
        "id" : "OUTGOINGPanel",
        "saveHandler" : OutgoingSaveHandler,
        "deleteHandler" : OutgoingDeleteHandler,
        "displayName" : u"OUTGOING_DESCRIPTION",
        "description" : _(u"Outgoing mail"),
        "callbacks" : (("OUTGOING_DISCOVERY", "OnOutgoingDiscovery"),),
        "messages" : ("OUTGOING_MESSAGE",),
    },
    "SHARING_DAV" : {
        "fields" : {
            "DAV_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default": _(u"New Sharing Account"),
            },
            "DAV_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "DAV_PATH" : {
                "attr" : "path",
                "type" : "string",
            },
            "DAV_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "DAV_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },
            "DAV_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 80,
                "required" : True,
            },
            "DAV_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
                "linkedTo" :
                        ("DAV_PORT", { True:"443", False:"80" }),
            },
        },
        "id" : "DAVPanel",
        "deleteHandler" : SharingDeleteHandler,
        "displayName" : "DAV_DESCRIPTION",
        "description" : _(u"Sharing"),
        "messages" : ("SHARING_MESSAGE", "SHARING_MESSAGE2"),
    },
    "SHARING_MORSECODE" : {
        "fields" : {
            "MORSECODE_DESCRIPTION" : {
                "attr" : "displayName",
                "type" : "string",
                "required" : True,
                "default": _(u"New Experimental Cosmo Account"),
            },
            "MORSECODE_SERVER" : {
                "attr" : "host",
                "type" : "string",
            },
            "MORSECODE_PATH" : {
                "attr" : "path",
                "type" : "string",
                "default": "/cosmo",
            },
            "MORSECODE_USERNAME" : {
                "attr" : "username",
                "type" : "string",
            },
            "MORSECODE_PASSWORD" : {
                "attr" : "password",
                "type" : "string",
            },
            "MORSECODE_PORT" : {
                "attr" : "port",
                "type" : "integer",
                "default": 80,
                "required" : True,
            },
            "MORSECODE_USE_SSL" : {
                "attr" : "useSSL",
                "type" : "boolean",
                "linkedTo" :
                        ("MORSECODE_PORT", { True:"443", False:"80" }),
            },
        },
        "id" : "MORSECODEPanel",
        "deleteHandler" : SharingDeleteHandler,
        "displayName" : "MORSECODE_DESCRIPTION",
        "description" : _(u"Sharing (Experimental)"),
        "messages" : ("SHARING_MESSAGE", "SHARING_MESSAGE2"),
    },
}


# Generic defaults based on the attr type.  Use "default" on attr for
# specific defaults.
DEFAULTS = {'string': '', 'integer': 0, 'boolean': False}

class AccountPreferencesDialog(wx.Dialog):

    def __init__(self, parent, title, size=wx.DefaultSize,
         pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE, resources=None,
         account=None, rv=None, modal=True):

        wx.Dialog.__init__(self, parent, -1, title, pos, size, style)

        self.resources = resources
        self.rv = rv
        self.modal = modal

        # outerSizer will have two children to manage: on top is innerSizer,
        # and below that is the okCancelSizer
        self.outerSizer = wx.BoxSizer(wx.VERTICAL)

        self.innerSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.accountsPanel = self.resources.LoadPanel(self, "AccountsPanel")
        self.innerSizer.Add(self.accountsPanel, 0, wx.ALIGN_TOP|wx.ALL, 5)

        self.outerSizer.Add(self.innerSizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.messagesPanel = self.resources.LoadPanel(self, "MessagesPanel")
        self.okCancelPanel = self.resources.LoadPanel(self, "OkCancelPanel")

        # The tmp panel and tmp sizer are used to force the messagePanel to
        # maintain a specific size regardless of what text is showing.
        # There is a bug in the HyperLinkCtrl related to layout that
        # was preventing using Sizer objects in the messagesPanel.
        self.tmpSizer = wx.BoxSizer(wx.VERTICAL)
        self.tmpPanel = self.resources.LoadPanel(self, "TmpPanel")
        self.tmpSizer.Add(self.messagesPanel, 0, wx.ALIGN_TOP|wx.ALL, 0)
        self.tmpSizer.Add(self.tmpPanel, 0, wx.ALIGN_TOP|wx.ALL, 0)
        self.bottomSizer.Add(self.tmpSizer, 0, wx.ALIGN_TOP|wx.ALL, 5)

        self.bottomSizer.Add(self.okCancelPanel, 0, wx.ALIGN_TOP|wx.ALL, 5)
        self.outerSizer.Add(self.bottomSizer, 0, wx.ALIGN_TOP|wx.ALIGN_LEFT|wx.ALL, 0)

        # Load the various account form panels:
        self.panels = {}
        #isMac = Utility.getPlatformName().startswith("Mac")

        for (key, value) in PANELS.iteritems():
            self.panels[key] = self.resources.LoadPanel(self, value['id'])

            #if isMac:
            #    self.panels[key].SetWindowVariant(wx.WINDOW_VARIANT_LARGE)


            self.panels[key].Hide()

        # These are wxHyperlinkCtrl widgets
        self.folderLink = wx.xrc.XRCCTRL(self, "INCOMING_FOLDERS_VERBAGE2")
        self.sharingLink = wx.xrc.XRCCTRL(self.messagesPanel, "SHARING_MESSAGE2")

        for hyperCtrl in (self.folderLink, self.sharingLink):
            hyperCtrl.SetNormalColour("#0080ff")
            hyperCtrl.SetVisitedColour("#0080ff")
            hyperCtrl.SetHoverColour("#9999cc")

        self.folderLink.SetURL(FOLDERS_URL)
        self.sharingLink.SetURL(SHARING_URL)


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

        #XXX There is a bug in the wx code that prevents
        #    a wx.HyperlinkCtrl from being hidden via
        #    xrc so the Hide() method is called by
        #    putting the sharingLink widget in
        #    the currentMessages list
        self.currentMessages = (self.sharingLink,)

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

        self.Bind(wx.EVT_CHOICE, self.OnToggleIncomingProtocol,
                  id=wx.xrc.XRCID("INCOMING_PROTOCOL"))

        self.Bind(wx.EVT_BUTTON, self.OnIncomingFolders,
                  id=wx.xrc.XRCID("INCOMING_FOLDERS"))

        self.Bind(wx.EVT_BUTTON, self.OnOk, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

        self.Bind(wx.EVT_BUTTON, self.OnTestAccount,
                      id=wx.xrc.XRCID("ACCOUNT_TEST"))

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

    def isDefaultAccount(self, item):
        isDefault = False

        if item.accountType == "INCOMING":
            ns_pim = schema.ns('osaf.pim', item.itsView)
            isDefault = item == ns_pim.currentIncomingAccount.item

        elif item.accountType == "OUTGOING":
            ns_pim = schema.ns('osaf.pim', item.itsView)
            isDefault = item == ns_pim.currentOutgoingAccount.item

        elif item.accountType in ("SHARING_DAV", "SHARING_MORSECODE"):
            sharing_ns = schema.ns('osaf.sharing', item.itsView)

            isDefault = item == sharing_ns.currentSharingAccount.item

        return isDefault

    def getDefaultAccounts(self):
        ns_pim = schema.ns('osaf.pim', self.rv)
        sharing_ns = schema.ns('osaf.sharing', self.rv)

        incoming  = ns_pim.currentIncomingAccount.item
        outgoing  = ns_pim.currentOutgoingAccount.item
        sharing   = sharing_ns.currentSharingAccount.item

        return (incoming, outgoing, sharing)


    def getAccountName(self, item):
        if self.isDefaultAccount(item):
            return _(u"%(accountName)s (Default)") % \
                       {'accountName': item.displayName}

        return item.displayName

    def selectAccount(self, accountIndex):
        self.accountsList.SetSelection(accountIndex)
        self.__SwapDetailPanel(accountIndex)

        item = self.rv.findUUID(self.data[accountIndex]['item'])

        delButton = wx.xrc.XRCCTRL(self, "BUTTON_DELETE")

        #Disable the delete button if the account is the
        #default.
        delButton.Enable(not self.isDefaultAccount(item))


    def __PopulateAccountsList(self, account):
        """ Find all account items and put them in the list; also build
            up a data structure with the applicable attribute values we'll
            be editing. If account is passed in, show its details. """

        # Make sure we're sync'ed with any changes other threads have made
        self.rv.refresh()
        accountIndex = 0 # which account to select first
        accounts = []

        #add the default accounts first
        for item in self.getDefaultAccounts():
            accounts.append(item)

        for cls in (Mail.IMAPAccount, Mail.POPAccount, Mail.SMTPAccount):
            for item in cls.iterItems(self.rv):
                if item.isActive and hasattr(item, 'displayName') and \
                    not self.isDefaultAccount(item):
                    accounts.append(item)

        for item in sharing.SharingAccount.iterItems(self.rv):
            if hasattr(item, 'displayName') and not \
               self.isDefaultAccount(item):
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
                    ns = schema.ns(desc['ns'], self.rv)
                    ref = getattr(ns, desc['pointer'])
                    setting = (ref.item == item)

                elif desc['type'] == 'itemRef':
                    # Store an itemRef as a UUID
                    try:
                        setting = getattr(item, desc['attr']).itsUUID
                    except AttributeError:
                        setting = None

                elif desc['type'] == 'chandlerFolders':
                    if item.accountProtocol == "IMAP":
                        setting = {"hasFolders": self.hasChandlerFolders(item)}
                    else:
                        setting = {}

                else:
                    # Otherwise store a literal
                    try:
                        setting = getattr(item, desc['attr'])
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
                                "protocol": item.accountProtocol,
                                "isNew"  : False } )

            self.accountsList.Append(self.getAccountName(item))

            i += 1
            # End of account loop

        if i > 0:
            self.selectAccount(accountIndex)


    def __ApplyChanges(self):
        """ Take the data from the list and apply the values to the items. """

        # First store the current form values to the data structure
        self.__StoreFormData(self.currentPanelType,
                             self.currentPanel,
                             self.data[self.currentIndex]['values'])

        if DEBUG:
            counter = 0

        for account in self.data:
            uuid = account['item']

            if uuid:
                # We already have an account item created
                item = self.rv.findUUID(account['item'])

            else:
                # We need to create an account item

                if account['protocol'] == "IMAP":
                    item = Mail.IMAPAccount(itsView=self.rv)

                elif account['protocol'] == "POP":
                    item = Mail.POPAccount(itsView=self.rv)

                elif account['protocol'] == "SMTP":
                    item = Mail.SMTPAccount(itsView=self.rv)

                elif account['protocol'] == "WebDAV":
                    item = sharing.WebDAVAccount(itsView=self.rv)

                elif account['protocol'] == "Morsecode":
                    item = sharing.CosmoAccount(itsView=self.rv)

            values = account['values']
            panel = PANELS[account['type']]

            if panel.has_key("saveHandler"):
                # Call custom save handler; if None returned, we don't do
                # any more processing of that account within this loop
                item = panel["saveHandler"](item, panel['fields'], values)

            if item is not None:
                if DEBUG:
                    # This stores the account which could have
                    # changed based on the results of the
                    # saveHandler to the data list.
                    # This info is only needed for
                    # debugging account saving.
                    self.data[counter]['item'] = item.itsUUID
                    counter += 1

                # Process each field defined in the PANEL data structure;
                # applying the values to the appropriate attributes:

                for (field, desc) in panel['fields'].iteritems():

                    if desc['type'] == 'currentPointer':
                        # If this value is True, make this item current:
                        if values[field]:
                            ns = schema.ns(desc['ns'], self.rv)
                            ref = getattr(ns, desc['pointer'])
                            ref.item = item

                    elif desc['type'] == 'itemRef':
                        # Find the item for this UUID and assign the itemref:
                        if values[field]:
                            setattr(item, desc['attr'],
                                    self.rv.findUUID(values[field]))

                    elif desc['type'] == 'chandlerFolders':
                       if values['INCOMING_PROTOCOL'] != "IMAP":
                           continue

                       action = values[field].get("action", None)

                       if action == "ADD" and not \
                             self.hasChandlerFolders(item):
                           folderNames = values[field]["folderNames"]
                           self.addChandlerFolders(item, folderNames)

                       elif action == "REMOVE" and \
                              self.hasChandlerFolders(item):
                           self.removeChandlerFolders(item)
                    else:
                        # Otherwise, make the literal assignment:
                        try:
                            val = values[field]

                            if val is None:
                                # wx controls require unicode
                                # or str values and will raise an
                                # error if passed None
                                val = u""

                            setattr(item, desc['attr'], val)
                        except AttributeError:
                            pass


    def __ApplyDeletions(self):
        # Since we don't delete items right away, we need to do it here:

        for data in self.deletions:
            uuid = data['item']

            if uuid:
                item = self.rv.findUUID(uuid)

                # Remove any folders in the IMAPAccount
                folders = getattr(item, "folders", None)

                if folders:
                    for folder in folders:
                        folders.remove(folder)
                        folder.delete()

                item.delete()

    def __ApplyCancellations(self):
        self.__StoreFormData(self.currentPanelType,
                             self.currentPanel,
                             self.data[self.currentIndex]['values'])

        # The only thing we need to do on Cancel is to remove any account items
        # we created this session:

        for account in self.data:
            if account['isNew']:
                uuid = account['item']
                item = self.rv.findUUID(uuid)
                item.delete()

            elif account['type'] == "INCOMING":
                #If there are pending changes on Chandler IMAP Folders
                # that have already been carried out on the server then
                # we need to store those changed values even on a cancel
                # since the operation was already performed.

                values = account['values']

                if values['INCOMING_PROTOCOL'] != "IMAP":
                    continue

                item = self.rv.findUUID(account['item'])

                action = values['INCOMING_FOLDERS'].get("action", None)

                if action == "ADD" and not self.hasChandlerFolders(item):
                    folderNames = values['INCOMING_FOLDERS']["folderNames"]
                    self.addChandlerFolders(item, folderNames)

                elif action == "REMOVE" and self.hasChandlerFolders(item):
                    self.removeChandlerFolders(item)

    def __Validate(self):
        # Call any custom validation handlers that might be defined

        # First store the current form values to the data structure
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
         self.data[self.currentIndex]['values'])

        i = 0

        for account in self.data:

            uuid = account['item']

            if uuid:
                item = self.rv.findUUID(uuid)

            else:
                item = None

            values = account['values']
            panel = PANELS[account['type']]

            if panel.has_key("validationHandler"):

                invalidMessage = panel["validationHandler"](item,
                    panel['fields'], values)

                if invalidMessage:
                    # Show the invalid panel
                    self.selectAccount(i)
                    alertError(invalidMessage)
                    return False

            i += 1

        return True


    def __GetDisplayName(self, index):
        # Each panel type has a field that is designated the displayName; this
        # method determines which field is the displayName, then gets the value

        data = self.data[self.currentIndex]
        accountType = data['type']
        panel = PANELS[accountType]
        values = data['values']
        item = self.rv.findUUID(data['item'])
        displayName = values[panel["displayName"]]

        if self.isDefaultAccount(item):
            return _(u"%(accountName)s (Default)") % \
                       {'accountName': displayName}

        return displayName

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


        init = PANELS[self.currentPanelType].get("init", None)

        self.__FetchFormData(self.currentPanelType, self.currentPanel,
         self.data[index]['values'])

        if init:
            cb = getattr(self, init, None)
            cb and cb()

        self.innerSizer.Add(self.currentPanel, 0, wx.ALIGN_TOP|wx.ALL, 5)
        self.currentPanel.Show()

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

        for messageWidget in self.currentMessages:
            messageWidget.Hide()

        self.currentMessages = []

        for message in PANELS[self.currentPanelType].get('messages', ()):
             messageWidget = wx.xrc.XRCCTRL(self.messagesPanel, message)
             messageWidget.Show()

             self.currentMessages.append(messageWidget)

        self.resizeLayout()


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

            elif valueType == "chandlerFolders":
               # The action and folderNames have
               # already been stored via callbacks
               # so do not do anything here
               continue

            elif valueType == "choice":
                index = control.GetSelection()

                if index == -1:
                    val = None
                else:
                    val = control.GetString(index)

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
                # The control can not accept a None value
                val = data[field] and data[field] or u""

                control.SetValue(val)

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

            elif valueType == "choice":
                pos = control.FindString(data[field])

                if pos != wx.NOT_FOUND:
                    control.SetSelection(pos)

            elif valueType == "chandlerFolders":
                if data["INCOMING_PROTOCOL"] == "IMAP":
                    hasFolders = data[field].get("hasFolders", False)
                    data['INCOMING_FOLDERS']['create'] = not hasFolders
                    control.SetLabel(self.getButtonVerbage(hasFolders))
                    control.GetContainingSizer().Layout()
                else:
                    control.SetLabel(CREATE_TEXT)
                    control.GetContainingSizer().Layout()


            # Handle itemrefs, which are stored as UUIDs.  We need to find
            # all items of the kind specified in the PANEL, filtering out those
            # which have been marked for deletion, or are inactive.
            elif valueType == "itemRef":
                items = []
                count = 0
                index = -1
                uuid = data[field]
                kindClass = PANELS[panelType]['fields'][field]['kind']
                for item in kindClass.iterItems(self.rv):
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
            if self.modal:
                self.EndModal(True)
            self.rv.commit()

            if DEBUG:
                self.debugAccountSaving()

            Globals.mailService.refreshMailServiceCache()
            self.Destroy()

    def debugAccountSaving(self):
        buf = ["\n"]
        ns_pim = schema.ns('osaf.pim', self.rv)
        sharing_ns = schema.ns('osaf.sharing', self.rv)

        currentOutgoing = ns_pim.currentOutgoingAccount.item
        currentIncoming = ns_pim.currentIncomingAccount.item
        currentSharing =  sharing_ns.currentSharingAccount.item

        for account in self.data:
            item = self.rv.findUUID(account['item'])

            buf.append(item.displayName)
            buf.append("=" * 35)
            buf.append("host: %s" % item.host)
            buf.append("port: %s" % item.port)
            buf.append("username: %s" % item.username)
            buf.append("password: %s" % item.password)

            if item.accountType in ("SHARING_DAV", "SHARING_MORSECODE"):
                buf.append("useSSL: %s" % item.useSSL)
                buf.append("path: %s" % item.path)

                if item == currentSharing:
                    buf.append("CURRENT: True")


            elif item.accountType == "INCOMING":
                buf.append("protocol %s" % item.accountProtocol)
                buf.append("security: %s" % item.connectionSecurity)
                buf.append("name: %s" % getattr(item, "fullName", ""))
                buf.append("email: %s" % getattr(item, "emailAddress", ""))

                folders = getattr(item, "folders", None)

                if folders:
                    buf.append("\nFOLDERS:")

                    for folder in folders:
                        buf.append("\tname: %s" % folder.displayName)
                        buf.append("\tIMAP name: %s" % folder.folderName)
                        buf.append("\ttype: %s" % folder.folderType)

                if item == currentIncoming:
                    buf.append("CURRENT: True")

            elif item.accountType == "OUTGOING":
                buf.append("security: %s" % item.connectionSecurity)
                buf.append("useAuth: %s" % item.useAuth)
                buf.append("email: %s" % getattr(item, "emailAddress", ""))

                if item == currentOutgoing:
                    buf.append("CURRENT: True")

            buf.append("\n")

        print (u"\n".join(buf)).encode("utf-8")


    def OnCancel(self, evt):
        self.__ApplyCancellations()
        self.rv.commit()
        if self.modal:
            self.EndModal(False)
        self.Destroy()

    def OnIncomingFolders(self, evt):
        if Globals.options.offline:
            return alertOffline()

        if not self.incomingAccountValid():
            return

        data = self.data[self.currentIndex]['values']

        button  = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_FOLDERS")
        create  = data['INCOMING_FOLDERS']['create']
        account = self.getIncomingAccount()

        if create:
            config = showConfigureDialog(CREATE_FOLDERS_TITLE,
                                  CREATE_FOLDERS % {'host': account.host})

            if config:
                ChandlerIMAPFoldersDialog(account, self.OnFolderCreation)
        else:
            yes = alertYesNo(REMOVE_FOLDERS_TITLE,
                             REMOVE_FOLDERS % {'host': account.host})

            if yes:
                RemoveChandlerIMAPFoldersDialog(account, self.OnFolderRemoval)

    def OnFolderCreation(self, result):
        statusCode, folderNames = result

        # Failure
        if statusCode == 0:
            # Since no folders created just return
            return

        button = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_FOLDERS")

        # It worked so set the text to remove folders
        button.SetLabel(REMOVE_TEXT)
        button.GetContainingSizer().Layout()

        data = self.data[self.currentIndex]['values']

        data['INCOMING_FOLDERS']['create'] = False
        data['INCOMING_FOLDERS']['action'] = "ADD"
        data['INCOMING_FOLDERS']['folderNames'] = folderNames
        data['INCOMING_FOLDERS']['hasFolders'] = True


    def OnFolderRemoval(self, result):
        statusCode, folderNames = result
        button = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_FOLDERS")

        # Failure
        if statusCode == 0:
            # Since folders still exist just return
            return

        # It worked so set the checkbox to false
        button.SetLabel(CREATE_TEXT)
        button.GetContainingSizer().Layout()

        data = self.data[self.currentIndex]['values']

        data['INCOMING_FOLDERS']['create'] = True
        data['INCOMING_FOLDERS']['action'] = "REMOVE"
        data['INCOMING_FOLDERS']['folderNames'] = folderNames
        data['INCOMING_FOLDERS']['hasFolders'] = False

    def OnAutoDiscovery(self, account):
        if account.accountType == "INCOMING":
            proto = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_PROTOCOL")
            if account.accountProtocol == "IMAP":
                proto.SetSelection(0)
            else:
                proto.SetSelection(1)

            port = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_PORT")
            port.SetValue(str(account.port))

            fieldInfo = PANELS[self.currentPanelType]['fields']['INCOMING_SECURE']

            for (button, value) in fieldInfo['buttons'].iteritems():
                if account.connectionSecurity == value:
                    control = wx.xrc.XRCCTRL(self.currentPanel, button)
                    control.SetValue(True)
                    break

            self.toggleIncomingFolders(account.accountProtocol=="IMAP")

        elif account.accountType == "OUTGOING":
            port = wx.xrc.XRCCTRL(self.currentPanel, "OUTGOING_PORT")
            port.SetValue(str(account.port))

            fieldInfo = PANELS[self.currentPanelType]['fields']['OUTGOING_SECURE']

            for (button, value) in fieldInfo['buttons'].iteritems():
                if account.connectionSecurity == value:
                    control = wx.xrc.XRCCTRL(self.currentPanel, button)
                    control.SetValue(True)
                    break
        else:
            # If this code is reached then there is a
            # bug which needs to be fixed.
            raise Exception("Internal Exception")

    def OnToggleIncomingProtocol(self, evt):
        proto = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_PROTOCOL")
        port = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_PORT")

        IMAP = proto.GetSelection() == 0

        fieldInfo = PANELS[self.currentPanelType]['fields']['INCOMING_SECURE']

        connectionSecurity = None

        for (button, value) in fieldInfo['buttons'].iteritems():
            control = wx.xrc.XRCCTRL(self.currentPanel, button)
            if control.GetValue():
                connectionSecurity = value
                break

        linkedTo = fieldInfo.get('linkedTo', None)

        if linkedTo is not None:
            imapDict = linkedTo['protocols']["IMAP"][1]
            popDict  = linkedTo['protocols']["POP"][1]

        if IMAP:
            if port.GetValue() in popDict.values():
                port.SetValue(imapDict[connectionSecurity])

            data = self.data[self.currentIndex]['values']

            button = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_FOLDERS")
            hasFolders = data["INCOMING_FOLDERS"].get("hasFolders", False)
            data["INCOMING_FOLDERS"]["create"] = not hasFolders
            button.SetLabel(self.getButtonVerbage(hasFolders))
            button.GetContainingSizer().Layout()

        else:
            if port.GetValue() in imapDict.values():
                port.SetValue(popDict[connectionSecurity])

        self.toggleIncomingFolders(IMAP)


    def getButtonVerbage(self, hasFolders):
        if hasFolders:
            return REMOVE_TEXT
        return CREATE_TEXT

    def initIncomingPanel(self):
        self.toggleIncomingFolders(self.getIncomingProtocol() == "IMAP", False)

    def toggleIncomingFolders(self, show=True, resize=True):
        widgets = ("INCOMING_FOLDERS", "INCOMING_FOLDERS_VERBAGE",
                   "INCOMING_FOLDERS_VERBAGE2", "INCOMING_FOLDERS_BUFFER",
                   "INCOMING_FOLDERS_BUFFER2")

        for widgetName in widgets:
            widget = wx.xrc.XRCCTRL(self.currentPanel, widgetName)

            if show:
                widget.Show()
            else:
                widget.Hide()

        if resize:
            self.resizeLayout()


    def OnNewAccount(self, evt):
        selection = self.choiceNewType.GetSelection()
        if selection == 0:
            return

        accountType = self.choiceNewType.GetClientData(selection)
        self.choiceNewType.SetSelection(0)

        if accountType == "INCOMING":
            item = Mail.IMAPAccount(itsView=self.rv)
            a = _(u"New Incoming Mail Account")
            p = "IMAP"
        elif accountType == "OUTGOING":
            item = Mail.SMTPAccount(itsView=self.rv)
            a = _(u"New Outgoing Mail Account")
            p = "SMTP"
        elif accountType == "SHARING_DAV":
            item = sharing.WebDAVAccount(itsView=self.rv)
            a = _(u"New Sharing Account")
            p = "WebDAV"
        elif accountType == "SHARING_MORSECODE":
            item = sharing.CosmoAccount(itsView=self.rv)
            a = _(u"New Chandler Hub Account")
            p = "Morsecode"

        item.displayName = a

        values = { }

        for (field, desc) in PANELS[accountType]['fields'].iteritems():

            if desc['type'] == 'currentPointer':
                setting = False

            elif desc['type'] == 'itemRef':
                setting = None

            elif desc['type'] == 'chandlerFolders':
                if p == "IMAP":
                    setting = {"hasFolders": self.hasChandlerFolders(item)}
                else:
                    setting = {}
            else:
                try:
                    setting = desc['default']
                except KeyError:
                    setting = DEFAULTS[desc['type']]

            values[field] = setting

        self.data.append( { "item" : item.itsUUID,
                            "values" : values,
                            "type" : accountType,
                            "protocol" : p,
                            "isNew" : True } )

        index = self.accountsList.Append(self.getAccountName(item))
        self.selectAccount(index)


    def getSelectedAccount(self):
        index = self.accountsList.GetSelection()
        return self.rv.findUUID(self.data[index]['item'])

    def OnDeleteAccount(self, evt):
        # First, make sure any values that have been modified in the form
        # are stored:
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        index = self.accountsList.GetSelection()
        item = self.rv.findUUID(self.data[index]['item'])

        deleteHandler = PANELS[item.accountType]['deleteHandler']
        canDelete = deleteHandler(item, self.data[index]['values'], self.data)

        if canDelete:
            self.accountsList.Delete(index)
            self.deletions.append(self.data[index])
            del self.data[index]
            self.innerSizer.Detach(self.currentPanel)
            self.currentPanel.Hide()
            self.currentIndex = None
            self.selectAccount(0)


    def OnTestAccount(self, evt):
        account = self.getSelectedAccount()

        if account is None:
            # If this code is reached then there is a
            # bug which needs to be fixed.
            raise Exception("Internal Exception")

        if account.accountType == "INCOMING":
            self.OnTestIncoming()
        elif account.accountType  == "OUTGOING":
            self.OnTestOutgoing()
        elif account.accountType  == "SHARING_DAV":
            self.OnTestSharingDAV()
        elif account.accountType  == "SHARING_MORSECODE":
            self.OnTestSharingMorsecode()
        else:
            # If this code is reached then there is a
            # bug which needs to be fixed.
            raise Exception("Internal Exception")

    def OnIncomingDiscovery(self, evt):
        if Globals.options.offline:
            return alertOffline()

        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        host = data['INCOMING_SERVER']

        if len(host.strip()) == 0:
            s = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_SERVER")
            s.SetFocus()
            return alertError(HOST_REQUIRED)

        AutoDiscoveryDialog(host, False, self.rv, self.OnAutoDiscovery)

    def OnOutgoingDiscovery(self, evt):
        if Globals.options.offline:
            return alertOffline()

        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        host = data['OUTGOING_SERVER']

        if len(host.strip()) == 0:
            s = wx.xrc.XRCCTRL(self.currentPanel, "OUTGOING_SERVER")
            s.SetFocus()
            return alertError(HOST_REQUIRED)

        AutoDiscoveryDialog(host, True, self.rv, self.OnAutoDiscovery)

    def getIncomingAccount(self):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        proto = data["INCOMING_PROTOCOL"]

        if proto == "IMAP":
             account = schema.ns('osaf.app', self.rv).TestIMAPAccount
        elif proto == "POP":
             account = schema.ns('osaf.app', self.rv).TestPOPAccount
        else:
            # If this code is reached then there is a
            # bug which needs to be fixed.
            raise Exception("Internal Exception")

        account.displayName = data['INCOMING_DESCRIPTION']
        account.host = data['INCOMING_SERVER']
        account.port = data['INCOMING_PORT']
        account.connectionSecurity = data['INCOMING_SECURE']
        account.username = data['INCOMING_USERNAME']
        account.password = data['INCOMING_PASSWORD']

        self.rv.commit()

        return account

    def incomingAccountValid(self):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        host = data['INCOMING_SERVER']
        port = data['INCOMING_PORT']
        username = data['INCOMING_USERNAME']
        password = data['INCOMING_PASSWORD']

        error = False

        if len(host.strip()) == 0 or \
           len(username.strip()) == 0 or \
           len(password.strip()) == 0:

           error = True

        try:
            # Test that the port value is an integer
            int(port)
        except:
            error = True

        if error:
            alertError(FIELDS_REQUIRED)

        return not error

    def OnTestIncoming(self):
        if Globals.options.offline:
            return alertOffline()

        if self.incomingAccountValid():
            account = self.getIncomingAccount()
            MailTestDialog(account)

    def outgoingAccountValid(self):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        host = data['OUTGOING_SERVER']
        port = data['OUTGOING_PORT']
        useAuth = data['OUTGOING_USE_AUTH']
        username = data['OUTGOING_USERNAME']
        password = data['OUTGOING_PASSWORD']

        error = False
        errorType = 0

        if len(host.strip()) == 0:
           error = True

        try:
            # Test that the port value is an integer
            int(port)
        except:
            error = True

        if useAuth:
            if len(username.strip()) == 0 or \
               len(password.strip()) == 0:
                error = True
                errorType = 1

        if error:
            if errorType:
                alertError(FIELDS_REQUIRED)

            else:
                alertError(FIELDS_REQUIRED_ONE)

        return not error

    def OnTestOutgoing(self):
        if Globals.options.offline:
            return alertOffline()

        if not self.outgoingAccountValid():
            return

        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        account = schema.ns('osaf.app', self.rv).TestSMTPAccount
        account.displayName = data['OUTGOING_DESCRIPTION']
        account.host = data['OUTGOING_SERVER']
        account.port = data['OUTGOING_PORT']
        account.connectionSecurity = data['OUTGOING_SECURE']
        account.useAuth = data['OUTGOING_USE_AUTH']
        account.username = data['OUTGOING_USERNAME']
        account.password = data['OUTGOING_PASSWORD']

        self.rv.commit()

        MailTestDialog(account)

    def OnTestSharingDAV(self):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        displayName = data["DAV_DESCRIPTION"]
        host = data['DAV_SERVER']
        port = data['DAV_PORT']
        path = data['DAV_PATH']
        username = data['DAV_USERNAME']
        password = data['DAV_PASSWORD']
        useSSL = data['DAV_USE_SSL']

        error = False

        if len(host.strip()) == 0 or \
           len(username.strip()) == 0 or \
           len(password.strip()) == 0 or \
           len(path.strip()) == 0:

           error = True

        try:
            # Test that the port value is an integer
            int(port)
        except:
            error = True

        if error:
            return alertError(FIELDS_REQUIRED_TWO)

        SharingTestDialog(displayName, host, port, path, username,
                          password, useSSL, self.rv)

    def OnTestSharingMorsecode(self):
        self.__StoreFormData(self.currentPanelType, self.currentPanel,
                             self.data[self.currentIndex]['values'])

        data = self.data[self.currentIndex]['values']

        displayName = data["MORSECODE_DESCRIPTION"]
        host = data['MORSECODE_SERVER']
        port = data['MORSECODE_PORT']
        path = data['MORSECODE_PATH']
        username = data['MORSECODE_USERNAME']
        password = data['MORSECODE_PASSWORD']
        useSSL = data['MORSECODE_USE_SSL']

        error = False

        if len(host.strip()) == 0 or \
           len(username.strip()) == 0 or \
           len(password.strip()) == 0 or \
           len(path.strip()) == 0:

           error = True

        try:
            # Test that the port value is an integer
            int(port)
        except:
            error = True

        if error:
            return alertError(FIELDS_REQUIRED_TWO)

        SharingTestDialog(displayName, host, port, path, username,
                          password, useSSL, self.rv, morsecode=True)

    def OnAccountSel(self, evt):
        # Huh? This is always False!
        # if not evt.IsSelection(): return

        sel = evt.GetSelection()
        self.selectAccount(sel)

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
        data = self.data[self.currentIndex]['values']

        # Scan through fields, seeing if this control corresponds to one
        # If marked as linkedTo, change the linked field
        ##        "linkedTo" : ("INCOMING_PORT", { True:993, False:143 } )
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
                    if type(linkedTo) == dict:
                        allValues = []
                        for (protocol, linkedFields) in linkedTo['protocols'].iteritems():
                            for v in linkedFields[1].values():
                                allValues.append(v)

                        cb = getattr(self, linkedTo['callback'])
                        res = cb()
                        linkedTo = linkedTo['protocols'][res]
                        linkedField = linkedTo[0]
                        linkedValues = linkedTo[1]
                    else:
                        linkedField = linkedTo[0]
                        linkedValues = linkedTo[1]
                        allValues = linkedValues.values()


                    linkedControl = wx.xrc.XRCCTRL(self.currentPanel,
                                                   linkedField)
                    if linkedControl.GetValue() in allValues:
                        linkedControl.SetValue(linkedValues[value])
                break


    def getIncomingProtocol(self):
        proto = wx.xrc.XRCCTRL(self.currentPanel, "INCOMING_PROTOCOL")
        return proto.GetString(proto.GetSelection())

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

                            aPanel = PANELS[accountData['protocol']]
                            for (aField, aFieldInfo) in \
                                aPanel['fields'].iteritems():
                                if aFieldInfo.get('type') == 'currentPointer':
                                    if aFieldInfo.get('pointer', '') == \
                                        fieldInfo.get('pointer'):
                                            accountData['values'][aField] = \
                                                False
                        index += 1
                    break

    def resizeLayout(self):
        self.innerSizer.Layout()
        self.outerSizer.Layout()
        self.outerSizer.SetSizeHints(self)
        self.outerSizer.Fit(self)

    def hasChandlerFolders(self, account):
        found = 0

        for folder in account.folders:
            name = folder.displayName

            if name == constants.CHANDLER_MAIL_FOLDER or \
               name == constants.CHANDLER_TASKS_FOLDER or \
               name == constants.CHANDLER_EVENTS_FOLDER:
                found += 1

        # All three folders are in the account.folders list
        return found == 3

    def addChandlerFolders(self, account, folderNames):
        m = Mail.IMAPFolder(itsView=account.itsView)
        m.displayName = constants.CHANDLER_MAIL_FOLDER
        m.folderName  = folderNames[0]
        m.folderType  = "MAIL"

        t = Mail.IMAPFolder(itsView=account.itsView)
        t.displayName = constants.CHANDLER_TASKS_FOLDER
        t.folderName = folderNames[1]
        t.folderType = "TASK"

        e = Mail.IMAPFolder(itsView=account.itsView)
        e.displayName = constants.CHANDLER_EVENTS_FOLDER
        e.folderName = folderNames[2]
        e.folderType = "EVENT"

        account.folders.extend([m,e,t])

    def removeChandlerFolders(self, account):
        for folder in account.folders:
            name = folder.displayName

            if name == constants.CHANDLER_MAIL_FOLDER or \
               name == constants.CHANDLER_TASKS_FOLDER or \
               name == constants.CHANDLER_EVENTS_FOLDER:
               account.folders.remove(folder)
               folder.delete()

def ShowAccountPreferencesDialog(parent, account=None, rv=None, modal=True):

    # Parse the XRC resource file:
    xrcFile = os.path.join(Globals.chandlerDirectory,
     'application', 'dialogs', 'AccountPreferences.xrc')

    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)

    # Display the dialog:
    win = AccountPreferencesDialog(parent, _(u"Account Preferences"),
     resources=resources, account=account, rv=rv, modal=modal)

    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
        return win

def alertOffline():
    showOKDialog(_(u"Mail service offline"), constants.TEST_OFFLINE)

def alertError(msg):
    showOKDialog(_(u"Account Preferences error"), msg)

def alertYesNo(title, msg):
    return showYesNoDialog(title, msg)

