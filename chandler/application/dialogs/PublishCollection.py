import os
import wx
import wx.xrc
import application.Globals
from application.Globals import repository as repo
from application.Globals import parcelManager as pm
import osaf.mail.message
import osaf.mail.sharing
import application.dialogs.Util

DEFAULT_URL = "http://code-bear.com/dav"

class PublishCollectionDialog(wx.Dialog):
    def __init__(self, parent, resources, collection):
        pre = wx.PreDialog()
        self.resources = resources
        resources.LoadOnDialog(pre, parent, 'PublishCollectionDialog')
        self.this = pre.this
        self.parent = parent
        self.collection = collection

        self.urlLabel = wx.xrc.XRCCTRL(self, "ID_URL_LABEL")
        self.urlLabel.SetLabel("Publish collection '%s' to:" % \
         collection.displayName)

        self.urlText = wx.xrc.XRCCTRL(self, "ID_URL")
        self.urlText.SetValue("%s/%s" % (DEFAULT_URL, collection.itsUUID))

        self.inviteesText = wx.xrc.XRCCTRL(self, "ID_INVITEES")

        self.waitLabel = wx.xrc.XRCCTRL(self, "ID_WAIT")
        self.OkButton = wx.xrc.XRCCTRL(self, "OK_BUTTON")
        self.CancelButton = wx.xrc.XRCCTRL(self, "CANCEL_BUTTON")

        wx.EVT_BUTTON( self, wx.xrc.XRCID( "OK_BUTTON" ), self.OnOk )
        wx.EVT_BUTTON( self, wx.xrc.XRCID( "CANCEL_BUTTON" ), self.OnCancel )

    def OnOk(self, evt):
        self.waitLabel.SetLabel("")

        # validate email addresses
        invitees = self.inviteesText.GetValue()
        if invitees:
            invitees = invitees.split(",")
            badAddresses = []

            for invitee in invitees:
                if not osaf.mail.message.isValidEmailAddress(invitee):
                    badAddresses.append(invitee)

            size = len(badAddresses)

            if size > 0:
                a = size > 1 and "addresses" or "address"
                self.waitLabel.SetLabel("Invalid %s: %s" % \
                 (a, ', '.join(badAddresses)))
                return

        url = self.urlText.GetValue()
        self.waitLabel.SetLabel("Publishing, Please Wait...")

        osaf.framework.webdav.Dav.DAV(url).put(self.collection)

        if invitees:
            osaf.mail.sharing.sendInvitation(url, invitees)

        self.EndModal(True)

    def OnCancel(self, evt):
        self.EndModal(False)

def ShowPublishCollectionsDialog(parent, collection):
        xrcFile = os.path.join(application.Globals.chandlerDirectory,
         'application', 'dialogs', 'PublishCollection_wdr.xrc')
        resources = wx.xrc.XmlResource(xrcFile)
        frame = PublishCollectionDialog(parent, resources, collection)
        val = frame.ShowModal()
        frame.Destroy()
