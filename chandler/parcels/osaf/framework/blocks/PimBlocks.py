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
import time
from osaf import sharing
import osaf.pim.mail as Mail
from repository.item.Item import Item
from osaf.pim import ContentItem, Note, ContentCollection
import application.dialogs.Util as Util
from i18n import ChandlerMessageFactory as _
from osaf import messages
from osaf.usercollections import UserCollection
from osaf.framework.blocks import Block, BlockEvent, debugName, getProxiedItem
from application import schema
from chandlerdb.util.c import issingleref

# hack workaround for bug 4747
def FilterGone(list):
    return [x for x in list if not issingleref(x)]

"""
Chandler-specific Blocks
This probably belongs outside the osaf.framework.blocks hierarchy, but so
does the calendar and detail view stuff, and there ought to be a Chandler-
specific (not CPIA-generic) subclass of Table for the Summary view, and all
of them want to use some of what's here... for now, it's here.
"""

class FocusEventHandlers(Item):
    """ 
    Adds behavior to allow handling events for of a view's selected items, 
    if all the items selected can process the event. 
    Mixed into the Blocks that have selected items (DetailViewRoot, Table,
    CalendarCanvas).
    
    Currently we're adding all needed handlers to this class, so it will
    likely expand when we add handlers for messages like Print...
    """
    
    def __getSendabilityOf(self, item):
        """ Return the sendable state of this item """
        assert item is not None
        item = getattr(item, 'proxiedItem', item)
        getSendabilityMethod = getattr(type(item), "getSendability", None)
        return getSendabilityMethod is None and 'not' \
               or getSendabilityMethod(item)
    
    def __getSelectedItems(self, event=None):
        """ Get the list of items selected in this view. """
        # We need the list of selected items to enable Send or actually send 
        # them. Try several places:
        # If we were given an event, and it has 'items', we'll use that.
        if event is not None:
            selectedItems = event.arguments.get('items', None)
            if selectedItems is not None:
                return FilterGone(selectedItems)

        # Otherwise, try to get it from this block's widget (which will probably 
        # provide it from ItemClipboardHandler)
        widget = getattr(self, 'widget', None)
        if widget is not None:
            selectedItemsMethod = getattr(type(widget), "SelectedItems", None)
            if selectedItemsMethod is not None:
                return FilterGone(selectedItemsMethod(widget))
        
        # Failing that, we'll use the block ourself.
        selectedItemsMethod = getattr(type(self), "SelectedItems", None)
        if selectedItemsMethod is not None:
            return FilterGone(selectedItemsMethod(self))
        
        # Give up and return an empty list
        return []

    def __getProxiedSelectedItems(self, event=None):
        """ As above, but wrap with proxies if appropriate """
        return map(getProxiedItem, self.__getSelectedItems(event))

    def __getPrimaryCollection(self):
        """
        the primary collection is probably contentsCollection - that's the
        collection around which most remove/delete actions should
        occur. But in case that isn't set, we can just default to
        self.contents
        """
        collection = self.contentsCollection
        if collection is None and isinstance(self.contents, ContentCollection):
            collection = self.contents

        return collection

    def onSendShareItemEventUpdateUI(self, event):
        """ Generically enable Send-ing. """
        enabled = False
        label = messages.SEND
        selectedItems = self.__getSelectedItems()
        if len(selectedItems) > 0:
            # Collect the states of all the items, so that we can change the
            # label to "Sent" if they're all in that state.
            sendStates = set([ self.__getSendabilityOf(item) 
                               for item in selectedItems ])
            if len(sendStates) == 1:
                if 'sendable' in sendStates:
                    enabled = True
                ## @@@ This was used when we showed the collection detail 
                ## view; it can't happen now.
                #elif 'sharable' in sendStates:
                    #enabled = True
                    #label = _(u"Share")
                #elif 'resharable' in sendStates:
                    #enabled = True
                    #label = _(u"Send to new")                   
                elif 'sent' in sendStates:
                    # All the items we considered have already been sent.
                    label = _(u"Sent")
        
        event.arguments['Enable'] = enabled
        event.arguments['Text'] = label

    def onSendShareItemEvent(self, event):
        """ Send or share the selected items """
        selectedItems = self.__getProxiedSelectedItems(event)
        if len(selectedItems) == 0:
            return

        # Make sure we have an outbound account; returns False if the user
        # cancels out and we don't.
        if not sharing.ensureAccountSetUp(self.itsView, outboundMail=True):
            return

        sendableItems = [ item for item in selectedItems 
                          if self.__getSendabilityOf(item) == 'sendable' ]
        assert list(selectedItems) == sendableItems

        for item in sendableItems:
            # For now, make sure we've got a 'from' string.
            # @@@ BJS: this'll go away when we change 'from' to an
            # account picker popup.
            if isinstance (item, Mail.MailMessageMixin):
                if unicode(item.fromAddress).strip() == u'':
                    item.fromAddress = item.getCurrentMeEmailAddress()

            Block.Block.postEventByNameWithSender('SendMail', {'item': item})

    def onFocusTogglePrivateEvent(self, event):
        """
        Toggle the "private" attribute of all the selected items
        or of the items specified in the optional arguments of the event.
        """
        selectedItems = self.__getProxiedSelectedItems(event)
        if len(selectedItems) > 0:
            # if any item is shared, give a warning if marking it private
            for item in selectedItems:
                if not item.private and \
                   item.getSharedState() != ContentItem.UNSHARED:
                    # Marking a shared item as "private" could act weird...
                    # Are you sure?
                    caption = _(u"Change the privacy of a shared item?")
                    msg = _(u"Other people may be subscribed to share this item; " \
                            "are you sure you want to mark it as private?")
                    if Util.yesNo(wx.GetApp().mainFrame, caption, msg):
                        break
                    else:
                        return
            # change the private state for all items selected
            for item in selectedItems:
                item.private = not item.private
            
    def onFocusTogglePrivateEventUpdateUI(self, event):
        selectedItems = self.__getSelectedItems()
        if len(selectedItems) > 0:
            # Collect the states of all the items, so that we can change all
            # the items if they're all in the same state.
            states = [(isinstance(item, Note), getattr(item, 'private', None))
                      for item in selectedItems]
            # only enable for Notes and their subclasses (not collections, etc)
            isNote, isPrivate = states[0]
            enable = isNote and len(set(states)) == 1
            event.arguments['Enable'] = enable
            event.arguments['Check'] = enable and isPrivate

    def onFocusStampEvent(self, event):
        selectedItems = self.__getProxiedSelectedItems(event)
        kindParam = event.kindParameter
        stampClass = kindParam.getItemClass()
        if len(selectedItems) > 0:
            # we don't want to try to stamp non-Note content items (e.g. Collections)
            states = [ (isinstance(item, Note), isinstance(item, stampClass))
                             for item in selectedItems]
            isNote, isStamped = states[0]
            assert len(set(states)) == 1
            assert isNote
            # stamp all items selected
            if isStamped:
                operation = 'remove'
            else:
                operation = 'add'
            for item in selectedItems:
                item.StampKind(operation, event.kindParameter)

    def onFocusStampEventUpdateUI(self, event):
        selectedItems = self.__getSelectedItems()
        stampClass = event.kindParameter.getItemClass()
        if len(selectedItems) > 0:
            # Collect the states of all the items, so that we can change all
            # the items if they're all in the same state.
            states = [ (isinstance(item, Note), isinstance(item, stampClass))
                             for item in selectedItems]
            isNote, isStamped = states[0]
            # we don't want to try to stamp non-Note content items (e.g. Collections)
            enable = isNote and len(set(states)) == 1 # all Notes with the same states?
            event.arguments['Enable'] = enable
            event.arguments['Check'] = enable and isStamped

    def onRunSelectedScriptEvent(self, event):
        # Triggered from "Tests | Run a Script"
        items = self.__getSelectedItems()
        if len(items) > 0:
            for item in items:
                if hasattr(item, 'execute'):
                    # in case the user was just editing the script,
                    # ask the focus to finish changes, if it can
                    Block.Block.finishEdits()

                    # run the script from the item's body
                    item.execute()

    def onRunSelectedScriptEventUpdateUI(self, event):
        # Triggered from "Tests | Run a Script"
        items = self.__getSelectedItems()
        enable = False
        if len(items) > 0:
            states = [hasattr(item, 'execute') for item in items]
            canExecute = states[0]
            enable = canExecute and len(set(states)) == 1
        event.arguments ['Enable'] = enable
        if enable:
            menuTitle = _(u'Run "%(name)s"') % { 'name': item.about }
        else:
            menuTitle = _(u'Run a Script')
        event.arguments ['Text'] = menuTitle

    def CanRemove(self):
        """
        The spec is very complex here.  The basic idea, beyond basic
        read-onlyness and such, is that and item can be removed from a
        collection as long as it will continue to exist in some other
        obvious collection.

        I've tried to optimize this for the more common cases, so that
        we do the least amount of work the most often.
        """
        selectedCollection = self.__getPrimaryCollection()
        selection = self.__getSelectedItems()
        if not isValidSelection(selection, selectedCollection):
            return False

        app_ns = schema.ns('osaf.app', self.itsView)
        pim_ns = schema.ns('osaf.pim', self.itsView)

        # you can never 'remove' from the trash
        if selectedCollection is pim_ns.trashCollection:
            return False

        # for OOTB collections, you can only remove not-mine items
        if UserCollection(selectedCollection).outOfTheBoxCollection:
            return not AllItemsInCollection(selection, pim_ns.mine)

        # For "mine" collections, item is always removable
        isMineCollection = selectedCollection in pim_ns.mine.sources
        if isMineCollection:
            return True

        # for "not mine" collections, each item has to exist at least
        # somewhere else... but it's possible that each item exists in
        # a separate collection (i.e. every item of the selection may
        # not appear in a single 'other' collection)
        sidebarCollections = app_ns.sidebarCollection
        for selectedItem in selection:
            selectedItem = selectedItem.getMembershipItem()

            # after alpha2 this should be
            # for otherCollection in selectedItem.appearsIn':
            # ...and exclude allCollection and selectedCollection
            for otherCollection in sidebarCollections:
                
                if (otherCollection is selectedCollection or
                    UserCollection(otherCollection).outOfTheBoxCollection):
                    continue

                # found an 'other' collection, skip ahead to next
                # selectedItem
                if selectedItem in otherCollection:
                    break
            else:
                # as soon as we find any item that isn't in another
                # collection, bail.
                return False

        return True

    def CanDelete(self):
        """
        The trick here is that Deleting is really 'move to trash' -
        which means if you're deleting items, you're affecting their
        membership in other collections... so those collections can't be
        readonly
        """
        selectedCollection = self.__getPrimaryCollection()
        selection = self.__getSelectedItems()
        
        if not isValidSelection(selection, selectedCollection):
            return False

        app_ns = schema.ns('osaf.app', self.itsView)
        sidebarCollections = app_ns.sidebarCollection

        # Make sure that there are no items in the selection that are
        # in a readonly collection
        
        # pre-cache the readwrite collections in the sidebar
        readonlyCollections = [collection for collection in sidebarCollections
                               if sidebarCollections.isReadOnly()]
        
        for selectedItem in selection:
            selectedItem = selectedItem.getMembershipItem()
            for sidebarCollection in readonlyCollections:
                if selectedItem in sidebarCollection:
                    return False
                    
        return True
    
    def onRemoveEventUpdateUI(self, event):
        event.arguments['Enable'] = self.CanRemove()

    def onDeleteEventUpdateUI(self, event):
        event.arguments['Enable'] = self.CanDelete()

    def onRemoveEvent(self, event):
        """
        Actually perform a remove
        """

        # Destructive action, worth an extra assert
        assert self.CanRemove(), "Can't remove right now.. some updateUI logic may be broken"
        selectedCollection = self.__getPrimaryCollection()
        selection = self.__getSelectedItems()

        assert selectedCollection, "Can't remove without a primary collection!"
        
        trash = schema.ns('osaf.pim', self.itsView).trashCollection
        if selectedCollection == trash:
            for selectedItem in selection:
                selectedItem.delete()
        else:
            for selectedItem in selection:
                selectedItem.removeFromCollection(selectedCollection)

    def onDeleteEvent(self, event):
        # Destructive action, worth an extra assert
        assert self.CanDelete(), "Can't delete right now.. some updateUI logic may be broken"
        selectedCollection = self.__getPrimaryCollection()
        selection = self.__getSelectedItems()

        assert selectedCollection, "Can't delete without a primary collection!"

        trash = schema.ns('osaf.pim', self.itsView).trashCollection
        if selectedCollection == trash:
            for selectedItem in selection:
                selectedItem.delete()
        else:
            for selectedItem in selection:
                selectedItem.addToCollection(trash)

def AllItemsInCollection(items, collection):
    """
    Helper routine - Checks if all items actually exist in the
    collection, using getMembershipItem() to make sure the 'in' test
    is valid. 

    Should this be in ContentCollection? (not sure if thats
    appropriate or not.. -alecf)
    """
    for item in items:
        item = item.getMembershipItem()
        if item not in collection:
            return False
    return True
    
def isValidSelection(selection, selectedCollection):
    return (len(selection) != 0  and
            selectedCollection is not None and
            not selectedCollection.isReadOnly())
