__version__ = "$Revision: $"
__date__ = "$Date: $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import application.Globals as Globals
import time
from osaf import sharing
import osaf.pim.mail as Mail
from repository.item.Item import Item
from osaf.pim import ContentItem, Note
import application.dialogs.Util as Util
from i18n import OSAFMessageFactory as _
from osaf import messages
from osaf.framework.blocks import BlockEvent
from application import schema

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
        getSendabilityMethod = getattr(type(item), "getSendability", None)
        return getSendabilityMethod is None and 'not' \
               or getSendabilityMethod(item)
    
    def __getSelectedItems(self):
        """ Get the list of items selected in this view. """
        # We need the list of selected items to enable Send or actually send 
        # them. Try to get it from this block's widget (which will probably 
        # provide it from ItemClipboardHandler), and if that doesn't work, 
        # try the block itself. Returns [] if neither implements it; 
        # otherwise, returns the list.
        try:
            selectedItemsMethod = getattr(type(self.widget), "SelectedItems")
        except AttributeError:
            try:
                selectedItemsMethod = getattr(type(self), "SelectedItems")
            except AttributeError:
                return [] # no one to ask? Assume no selected items.
            else:
                selectedItems = selectedItemsMethod(self)
        else:
            selectedItems = selectedItemsMethod(self.widget)
        return selectedItems

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
        selectedItems = self.__getSelectedItems()
        if len(selectedItems) == 0:
            return

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not sharing.ensureAccountSetUp(self.itsView,
                                          inboundMail=True,
                                          outboundMail=True):
            return

        sendableItems = [ item for item in selectedItems 
                          if self.__getSendabilityOf(item) == 'sendable' ]
        assert list(selectedItems) == sendableItems
        for item in sendableItems:
            # For now, make sure we've got a 'from' string.
            # @@@ BJS: this'll go away when we change 'from' to an
            # account picker popup.
            if isinstance (item, Mail.MailMessageMixin):
                if item.ItemWhoFromString() == u'':
                    item.whoFrom = item.getCurrentMeEmailAddress()
            item.shareSend()

    def onFocusTogglePrivateEvent(self, event):
        """
        Toggle the "private" attribute of all the selected items
        or of the items specified in the optional arguments of the event.
        """
        selectedItems = event.arguments.get('items', self.__getSelectedItems())
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
        selectedItems = event.arguments.get('items', self.__getSelectedItems())
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
            # the Detail View gets upset when we stamp without giving it a chance to update
            self.postEventByName('ResyncDetailParent', {}) # workaround for bug 4091

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
                    focusedWidget = wx.Window_FindFocus()
                    try:
                        method = focusedWidget.blockItem.finishSelectionChanges()
                    except AttributeError:
                        pass
                    else:
                        method()
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
            menuTitle = u'Run "%s"\tCtrl+S' % item.about
        else:
            menuTitle = u'Run a Script\tCtrl+S'
        event.arguments ['Text'] = menuTitle


