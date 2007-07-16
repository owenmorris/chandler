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
#   limitations under the License.

import wx
import logging
import os, sys
from application import schema, Globals
from i18n import ChandlerMessageFactory as _
from application.dialogs.RecurrenceDialog import getProxy
from osaf import sharing

logger = logging.getLogger(__name__)

REMOVE_NORMAL           = 1
DELETE_DASHBOARD        = 2
DELETE_LAST             = 3
IN_READ_ONLY_COLLECTION = 4
READ_ONLY_SELECTED      = 5


DELETE_STATES = (DELETE_DASHBOARD, DELETE_LAST)

# structure is [itemState](title text, dialog text)
dialogTextData = {
    DELETE_DASHBOARD :
        (_(u"Remove from Dashboard"), 
         _(u"Removing '%(itemName)s' from the Dashboard will move it to the Trash.")),
    DELETE_LAST :
        (_(u"Only appearance of item"),
         _(u"'%(itemName)s' only appears in '%(collectionName)s'. Removing it will move it to the Trash.")),
    IN_READ_ONLY_COLLECTION :
        (_(u"View-only item"),
         _(u"You cannot delete '%(itemName)s'. "
           u"It belongs to the view-only collection '%(readOnlyCollectionName)s'.")),
    READ_ONLY_SELECTED :
        (_(u"View-only collection"),
         _(u"You cannot make changes to '%(collectionName)s'")),
}

def GetReadOnlyCollection(item, view):
    """Return the first read-only collection the item is in, or None."""
    app_ns = schema.ns('osaf.app', view)
    pim_ns = schema.ns('osaf.pim', view)
    allCollection = pim_ns.allCollection
    
    sidebarCollections = app_ns.sidebarCollection
    
    memberItem = getProxy(u'ui', item).getMembershipItem()
    for collection in [col for col in sidebarCollections if sharing.isReadOnly(col)]:
        if memberItem in collection:
            return collection
    return None

def GetItemRemovalState(selectedCollection, item, view):
    """
    Determine how an item that's supposed to be removed ought to be handled.

    It may be simply removed, or its collection membership may indicate that
    it should be deleted, or it could be treated as read-only.
    
    """
    app_ns = schema.ns('osaf.app', view)
    pim_ns = schema.ns('osaf.pim', view)
    allCollection = pim_ns.allCollection
    
    sidebarCollections = app_ns.sidebarCollection
    readonlyCollections = [col for col in sidebarCollections
                           if sharing.isReadOnly(col)]

    # you can always remove from the trash
    if selectedCollection is pim_ns.trashCollection:
        return REMOVE_NORMAL

    elif selectedCollection in readonlyCollections:
        return READ_ONLY_SELECTED

    else:
        memberItem = getProxy(u'ui', item).getMembershipItem()
        if selectedCollection is allCollection:
            # Items in the dashboard because they're in a mine collection
            # can't be removed, they're always deleted
            if GetReadOnlyCollection(item, view) is None:
                for collection in memberItem.collections or []:
                    if collection in pim_ns.mine.sources:
                        return DELETE_DASHBOARD
            else:
                return IN_READ_ONLY_COLLECTION

        if len(memberItem.appearsIn) > 1:
            return REMOVE_NORMAL
        else:
            return DELETE_LAST

def ShowDeleteDialog(view=None, selectedCollection=None,
                     itemsAndStates=None, originalAction='remove', modal=True):
    filename = 'DeleteDialog.xrc'
    xrcFile = os.path.join(Globals.chandlerDirectory,
                           'application', 'dialogs', filename)
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = DeleteDialog(resources=resources,
                       view=view,
                       selectedCollection=selectedCollection,
                       originalAction=originalAction,
                       modal=modal,
                       itemsAndStates=itemsAndStates)
    
    if win.rendered:
        win.CenterOnScreen()
        if modal:
            return win.ShowModal()
        else:
            win.Show()
            return win

class DeleteDialog(wx.Dialog):

    def __init__(self, resources=None, view=None, 
                 selectedCollection=None, originalAction='remove', modal=True,
                 itemsAndStates=None):

        self.resources = resources
        self.view = view
        self.selectedCollection = selectedCollection
        self.modal = modal
        self.itemsAndStates = itemsAndStates
        self.originalAction = originalAction
        
        # Apply to all checkbox states
        self.lastItemApplyAll   = False
        self.readOnlyApplyAll   = False
        self.dashboardRemoveAll = False

        # count whether Apply to alls should be shown
        self.countDict = {DELETE_DASHBOARD        : 0, 
                          DELETE_LAST             : 0,
                          IN_READ_ONLY_COLLECTION : 0,
                          READ_ONLY_SELECTED      : 0}

        for item, state in itemsAndStates:
            self.countDict[state] += 1

        # the item in itemsAndStates being worked with, incremented by
        # ProcessNextItem
        self.itemNumber = -1

        main_ns = schema.ns('osaf.views.main', view)

        dialogsToDisplay = 0
        if main_ns.dashboardRemovalPref.askNextTime:
            dialogsToDisplay += self.countDict[DELETE_DASHBOARD]
        if main_ns.lastCollectionRemovalPref.askNextTime:
            dialogsToDisplay += self.countDict[DELETE_LAST]
        dialogsToDisplay += self.countDict[IN_READ_ONLY_COLLECTION]
        dialogsToDisplay += self.countDict[READ_ONLY_SELECTED]
        
        if dialogsToDisplay > 0:
            pre = wx.PreDialog()
            self.resources.LoadOnDialog(pre, None, "DeleteDialog")
            self.PostCreate(pre)
            self.rendered = True
    
            self.text = wx.xrc.XRCCTRL(self, "Text")
            self.applyToAllCheckbox = wx.xrc.XRCCTRL(self, "ApplyAll")
            self.neverShowCheckbox = wx.xrc.XRCCTRL(self, "NeverShowAgain")
            
            self.Bind(wx.EVT_BUTTON, self.ProcessOK, id=wx.ID_OK)
            self.Bind(wx.EVT_BUTTON, self.OnDone, id=wx.ID_CANCEL)
            self.Bind(wx.EVT_BUTTON, self.ProcessDelete,
                      id=wx.xrc.XRCID("MoveToTrash"))
    
            self.Fit()
        else:
            self.rendered = False

        self.ProcessNextItem()
        

    def ProcessNextItem(self):
        main_ns = schema.ns('osaf.views.main', self.view)

        while True:
            self.itemNumber += 1
            if self.itemNumber >= len(self.itemsAndStates):
                self.OnDone()
            else:
                item, state = self.itemsAndStates[self.itemNumber]
                
                # ignoring applyToAll for now
                if state == DELETE_DASHBOARD:
                    if (self.dashboardRemoveAll or
                        not main_ns.dashboardRemovalPref.askNextTime):
                        self.DeleteItem()
                        continue
                    else:
                        self.DeletePrompt()
                elif state == DELETE_LAST:
                    if (self.lastItemApplyAll or
                        not main_ns.lastCollectionRemovalPref.askNextTime):
                        self.DeleteItem()
                        continue
                    else:
                        self.DeletePrompt()
                elif state == IN_READ_ONLY_COLLECTION:
                    if self.readOnlyApplyAll:
                        continue
                    else:
                        self.ReadOnlyPrompt()
                else:
                    self.ReadOnlyPrompt()
            break

    def GetTextDict(self):
        item, state = self.itemsAndStates[self.itemNumber]
        textDict = dict(collectionName = self.selectedCollection.displayName,
                        itemName       = item.displayName,
                        count          = self.countDict[state])
        if state == IN_READ_ONLY_COLLECTION:
            readOnlyCollection = GetReadOnlyCollection(item, self.view)
            textDict['readOnlyCollectionName'] = readOnlyCollection.displayName
        return textDict

    def SetText(self):
        item, state = self.itemsAndStates[self.itemNumber]
        textDict = self.GetTextDict()
        title, text = dialogTextData[state]
        
        self.applyToAllCheckbox.SetLabel(_(u"Apply to all (%(count)s)") % textDict)
        self.SetTitle(title % textDict)
        
        self.text.Show()
        self.text.SetLabel(text % textDict)
        self.text.Wrap(350)

    def ReadOnlyPrompt(self):
        self.AdjustButtons()

        item, state = self.itemsAndStates[self.itemNumber]        
        
        if state == IN_READ_ONLY_COLLECTION and self.countDict[state] > 1:
            self.applyToAllCheckbox.Show()
            self.applyToAllCheckbox.SetValue(False)
        else:
            self.applyToAllCheckbox.Hide()

        self.neverShowCheckbox.Hide()

        self.SetText()
            
        wx.xrc.XRCCTRL(self, "wxID_OK").SetFocus()
        self.Fit()
        wx.GetApp().Yield(True)

    def DeletePrompt(self):
        self.AdjustButtons()

        item, state = self.itemsAndStates[self.itemNumber]
        
        if self.countDict[state] > 1:
            self.applyToAllCheckbox.Show()
            self.applyToAllCheckbox.SetValue(False)
        else:
            self.applyToAllCheckbox.Hide()

        if state in DELETE_STATES:
            self.neverShowCheckbox.Show()
            self.neverShowCheckbox.SetValue(False)            
        else:
            self.neverShowCheckbox.Hide()
            
        self.SetText()

        wx.xrc.XRCCTRL(self, "MoveToTrash").SetFocus()
        self.Fit()
        wx.GetApp().Yield(True)

    def HandleApplyToAll(self):
        main_ns = schema.ns('osaf.views.main', self.view)
        state = self.itemsAndStates[self.itemNumber][1]
        self.countDict[state] -= 1
        if self.applyToAllCheckbox.IsShown() and self.applyToAllCheckbox.GetValue():
            if state == DELETE_DASHBOARD:
                self.dashboardRemoveAll = True
            elif state == DELETE_LAST:
                self.lastItemApplyAll = True
            elif state == IN_READ_ONLY_COLLECTION:
                self.readOnlyApplyAll = True
        
        if self.neverShowCheckbox.IsShown() and self.neverShowCheckbox.GetValue():
            if state == DELETE_DASHBOARD:
                main_ns.dashboardRemovalPref.askNextTime = False
            elif state == DELETE_LAST:
                main_ns.lastCollectionRemovalPref.askNextTime = False
        

    def ProcessOK(self, evt):
        if self.itemsAndStates[self.itemNumber][1] == READ_ONLY_SELECTED:
            # only prompt once if the selected collection is read only
            self.OnDone()
        else:
            self.HandleApplyToAll()
            self.ProcessNextItem()

    def DeleteItem(self):
        trash = schema.ns('osaf.pim', self.view).trashCollection
        proxiedItem = getProxy(u'ui', self.itemsAndStates[self.itemNumber][0])
        proxiedItem.addToCollection(trash)

    def ProcessDelete(self, evt=None):
        self.DeleteItem()
        self.HandleApplyToAll()
        self.ProcessNextItem()

    def OnDone(self, evt=None):
        if self.rendered:
            if self.modal:
                self.EndModal(False)
            self.Destroy()

    def AdjustButtons(self):
        state = self.itemsAndStates[self.itemNumber][1]
        if state in DELETE_STATES:
            wx.xrc.XRCCTRL(self, "wxID_CANCEL").Show()
            wx.xrc.XRCCTRL(self, "MoveToTrash").Show()
            wx.xrc.XRCCTRL(self,     "wxID_OK").Hide()
        else:
            wx.xrc.XRCCTRL(self, "wxID_CANCEL").Hide()
            wx.xrc.XRCCTRL(self, "MoveToTrash").Hide()
            wx.xrc.XRCCTRL(self,     "wxID_OK").Show()
