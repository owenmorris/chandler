#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from osaf import sharing
import osaf.pim.mail as Mail
from repository.item.Item import Item
from osaf.pim import EventStamp, Note, ContentCollection, has_stamp
from i18n import ChandlerMessageFactory as _
from osaf import messages
from osaf.framework.blocks import Block, getProxiedItem
from application import schema
from application.dialogs.RecurrenceDialog import (getProxy,
                                                  delayForRecurrenceDialog)
import application.dialogs.DeleteDialog as DeleteDialog
from chandlerdb.item.c import isitemref
from chandlerdb.item.ItemError import *

# hack workaround for bug 4747
def FilterGone(list):
    return [x for x in list if not isitemref(x)]

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
        if has_stamp(item, Mail.MailStamp):
            return Mail.MailStamp(item).getSendability()
        else:
            return 'not'
    
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
        if collection is None:
            contents = getattr(self, 'contents', None)
            if isinstance(contents, ContentCollection):
               collection = contents

        return collection

    def onSendShareItemEventUpdateUI(self, event):
        """ Generically enable Send-ing. """
        # default to a disabled "Send" with a send-arrow
        enabled = False
        label = messages.SEND
        bitmap = "ApplicationBarSend.png"
        selectedItems = self.__getSelectedItems()
        if len(selectedItems) > 0:
            # Collect the states of all the items, so that we can change the
            # label to "Sent" if they're all in that state.
            sendStates = set([ self.__getSendabilityOf(item) 
                               for item in selectedItems ])
            if len(sendStates) == 1:
                result = sendStates.pop()
                
                if result == 'send':
                    enabled = True
                elif result == 'update':
                    enabled = True
                    label = messages.UPDATE
                    # use U-shaped Update bitmap
                    bitmap = "ApplicationBarUpdate.png"
                elif result == 'sent':
                    label = messages.SENT

        event.arguments['Enable'] = enabled
        event.arguments['Text'] = label
        event.arguments['Bitmap'] = bitmap

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
                          if self.__getSendabilityOf(item) in ('send', 'update')
                        ]
        assert list(selectedItems) == sendableItems

        for item in sendableItems:
            # For now, make sure we've got a 'from' string.
            # @@@ BJS: this'll go away when we change 'from' to an
            # account picker popup.
            if has_stamp(item, Mail.MailStamp):
                mailObject = Mail.MailStamp(item)
                #XXX this should raise an error instead of
                # adding the me address since that results
                # in the incorrect sender getting added
                # which can confuse user
                if unicode(mailObject.fromAddress).strip() == u'':
                    mailObject.fromAddress = mailObject.getCurrentMeEmailAddress()

            Block.Block.postEventByNameWithSender('SendMail', {'item': item})

    def onMarkAsReadEvent(self, event):
        selectedItems = self.__getProxiedSelectedItems(event)
        for item in selectedItems:
            EventStamp(item).getMaster().itsItem.read = True

    def onFocusTogglePrivateEvent(self, event):
        """
        Toggle the "private" attribute of all the selected items
        or of the items specified in the optional arguments of the event.
        """
        selectedItems = self.__getProxiedSelectedItems(event)
        if len(selectedItems) > 0:
            # if any item is shared, give a warning if marking it private
            for item in selectedItems:
                if not item.private and sharing.isShared(item):
                    # Marking a shared item as "private" could act weird...
                    # Are you sure?
                    caption = _(u"Change the privacy of a shared item?")
                    msg = _(u"Other people may be subscribed to share this item; " \
                            "are you sure you want to mark it as private?")
                    if wx.MessageBox (msg, caption, style = wx.YES_NO,
                                      parent = wx.GetApp().mainFrame) == wx.YES:
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
        else:
            event.arguments['Enable'] = False
            event.arguments['Check'] = False

    # event and menu item defined in debug plugin
    def on_debug_CreateConflictEvent(self, event):
        selectedItems = self.__getSelectedItems()
        if len(selectedItems) > 0:
            for item in selectedItems:
                if not has_stamp(item, sharing.SharedItem):
                    sharing.SharedItem(item).add()
                sharing.SharedItem(item).generateConflicts()

    def onFocusStampEvent(self, event):
        selectedItems = self.__getProxiedSelectedItems(event)
        stampClass = event.classParameter
        if len(selectedItems) > 0:
            # we don't want to try to stamp non-Note content items (e.g. Collections)
            states = [ (isinstance(item, Note),
                        has_stamp(item, stampClass))
                             for item in selectedItems]
            isNote, isStamped = states[0]
            assert len(set(states)) == 1
            assert isNote
            # stamp all items selected
            if isStamped:
                def doit(item):
                    stampClass(item).remove()
            else:
                def doit(item):
                    stampClass(item).add()
                
            for item in selectedItems:
                doit(item)

    def onFocusStampEventUpdateUI(self, event):
        selectedItems = self.__getSelectedItems()
        stampClass = event.classParameter
        enable = False
        states = set()
        
        for item in selectedItems:
            # we don't want to try to stamp non-Note content items
            # (e.g. Collections)
            enable = (isinstance(item, Note) and 
                      item.isAttributeModifiable('body'))
            if not enable:
                break
                
            # Collect the states of all the items, so that we can change all
            # the items if they're all in the same state.
            states.add(has_stamp(item, stampClass))
        
        enable = enable and (len(states) == 1)

        event.arguments['Enable'] = enable
        # next() won't raise because len(status) is 1
        # event.arguments['Check'] = enable and iter(states).next()
        
        if enable:
            sender = event.arguments['sender']
            if iter(states).next():
                event.arguments['Text'] = sender.toggleTitle
            else:
                event.arguments['Text'] = sender.title


    def CanReplyOrForward(self, selectedItem):
        # We used to test for whether the message had ever been
        # received by the mail service ("in", sort of), but Mimi
        # thinks outgoing messages should be replyable too.
        # return has_stamp(selectedItem, Mail.MailStamp) and \
        #        Mail.MailStamp(selectedItem).viaMailService
        return has_stamp(selectedItem, Mail.MailStamp) and \
                Mail.MailStamp(selectedItem).getSendability() != 'not'

    def onReplyOrForwardEvent(self, replyMethod):
        Block.Block.finishEdits()
        
        item = None
        # Note that this skips over any non-inbox items, so you
        # *could* select-all-reply
        for selectedItem in self.__getSelectedItems():
            if self.CanReplyOrForward(selectedItem):
                item = selectedItem
                break
        
        if item is not None:
            delayForRecurrenceDialog(item,
                                     self._replyOrForward, item, replyMethod)
    
    def _replyOrForward(self, item, replyMethod):
        pim_ns = schema.ns('osaf.pim', self.itsView)
        main = schema.ns("osaf.views.main", self.itsView)

        if main.MainView.trashCollectionSelected():
            # Items can not be created in the Trash
            # collection
            return

        replyMessage = replyMethod(self.itsView, Mail.MailStamp(item))
        # select the outbox collection if there was a reply
        if replyMessage is not None:
            inCollection = pim_ns.inCollection

            if main.MainView.getSidebarSelectedCollection() is inCollection:
                # Replys and Forwards can not be created in the
                # In collection so move the selected sidebard collection
                # to the Dashboard
                sidebar = Block.Block.findBlockByName ("Sidebar")
                sidebar.select(pim_ns.allCollection)

            #add to dashboard by making mine
            pim_ns.allCollection.add(replyMessage)
            replyMessage.mine = True

            collection = main.MainView.getSidebarSelectedCollection()

            # Add the item to the current collection
            collection.add(replyMessage)

            # select the last message replied/forwarded
            main.MainView.selectItems([replyMessage])
            # by default the "from" field is selected, which looks funny;
            # so switch focus to the message body, except for "Forward",
            # which goes to the "To" field
            if replyMethod is not Mail.forwardMessage:
                focusTarget = Block.Block.findBlockByName('NotesBlock')
            else:
                focusTarget = Block.Block.findBlockByName('EditMailTo')
            if focusTarget is not None:
                focusTarget.widget.SetFocus()

    def onReplyOrForwardEventUpdateUI(self, event):
        selection = self.__getSelectedItems()
        enabled = len(selection) > 0
        if enabled:
            for selectedItem in selection:
                if not self.CanReplyOrForward(selectedItem):
                    enabled = False
                    break
        event.arguments['Enable'] = enabled

    def onReplyEvent(self, event):
        self.onReplyOrForwardEvent(Mail.replyToMessage)

    def onReplyEventUpdateUI(self, event):
        self.onReplyOrForwardEventUpdateUI(event)


    def onReplyAllEvent(self, event):
        self.onReplyOrForwardEvent(Mail.replyAllToMessage)

    def onReplyAllEventUpdateUI(self, event):
        self.onReplyOrForwardEventUpdateUI(event)


    def onForwardEvent(self, event):
        self.onReplyOrForwardEvent(Mail.forwardMessage)

    def onForwardEventUpdateUI(self, event):
        self.onReplyOrForwardEventUpdateUI(event)

    def CanDelete(self):
        """
        Deleting is really 'move to trash' - which means if you're deleting
        items, you're affecting their membership in other collections... so
        those collections can't be readonly.
        
        However, the current plan is to pop up a dialog if delete can't
        happen, so always allow delete if there's anything selected.
        
        """
        return isValidSelection(self.__getSelectedItems(),
                                self.__getPrimaryCollection())

    CanRemove = CanDelete

    def onRemoveEventUpdateUI(self, event):
        event.arguments['Enable'] = self.CanRemove()

    def onDeleteEventUpdateUI(self, event):
        event.arguments['Enable'] = self.CanDelete()

    def selectionEmptiedAfterDelete (self, selectedCollection, oldIndex):
            self.postEventByName("SelectItemsBroadcast",
                                 {'items': [],
                                  'collection': selectedCollection })

    def onRemoveEvent(self, event):
        """
        Actually perform a remove
        """
        selectedCollection = self.__getPrimaryCollection()
        selection = self.__getSelectedItems()
        assert len(selection) > 0 # If this assert fails fix onRemoveEventUpdateUI

        try:
            oldIndex = self.contents.index (selection[0])
        except NoSuchItemInCollectionError:
            oldIndex = None

        assert selectedCollection, "Can't remove without a primary collection!"

        itemsAndStates = []
        removals = []
        for item in selection:
            state = DeleteDialog.GetItemRemovalState(selectedCollection, item,
                                                     self.itsView)
            if state == DeleteDialog.REMOVE_NORMAL:
                removals.append(item)
            else:
                itemsAndStates.append((item, state))

        pim_ns = schema.ns('osaf.pim', self.itsView)
        if selectedCollection == pim_ns.trashCollection:
            def removeItem(item):
                # For deleting from the trash, get rid of the event's
                # master; there's no sense in asking about a particular
                # instance.
                getattr(item, 'inheritFrom', item).delete(True)
        else:
            def removeItem(item):
                item = getProxy(u'ui', item)
                item.removeFromCollection(selectedCollection)

        for item in removals:
            removeItem(item)
        
        if len(itemsAndStates) != 0:
            DeleteDialog.ShowDeleteDialog(view=self.itsView,
                                          selectedCollection=selectedCollection,
                                          itemsAndStates=itemsAndStates)            
        if self.contents.isSelectionEmpty():
            self.selectionEmptiedAfterDelete (selectedCollection, oldIndex)

    def onDeleteEvent(self, event):
        selectedCollection = self.__getPrimaryCollection()
        selection = self.__getSelectedItems()
        assert len(selection) > 0 # If this assert fails fix onDeleteEventUpdateUI
        
        try:
            oldIndex = self.contents.index (selection[0])
        except NoSuchItemInCollectionError:
            oldIndex = None

        assert selectedCollection, "Can't delete without a primary collection!"

        trash = schema.ns('osaf.pim', self.itsView).trashCollection
        if selectedCollection == trash:
            def deleteItem(item):
                # For deleting from the trash, get rid of the event's
                # master; there's no sense in asking about a particular
                # instance.
                getattr(item, 'inheritFrom', item).delete(True)
        else:
            def deleteItem(item):
                item.addToCollection(trash)
        
        readonly  = []
        for item in selection:
            if DeleteDialog.GetReadOnlyCollection(item, self.itsView) is None:
                deleteItem(getProxy(u'ui', item))
            else:
                readonly.append((item, DeleteDialog.IN_READ_ONLY_COLLECTION))

        if len(readonly) != 0:
            DeleteDialog.ShowDeleteDialog(view=self.itsView,
                                          selectedCollection=selectedCollection,
                                          itemsAndStates=readonly,
                                          originalAction='delete')            
        if self.contents.isSelectionEmpty():
            self.selectionEmptiedAfterDelete (selectedCollection, oldIndex)

                        
def isValidSelection(selection, selectedCollection):
    return (len(selection) != 0 and selectedCollection is not None)
