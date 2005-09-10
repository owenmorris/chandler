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
from i18n import OSAFMessageFactory as _

"""
Chandler-specific Blocks
This probably belongs outside the osaf.framework.blocks hierarchy, but so
does the calendar and detail view stuff, and there ought to be a Chandler-
specific (not CPIA-generic) subclass of Table for the Summary view, and all
of them want to use some of what's here... for now, it's here.
"""

class Sendability(Item):
    """ 
    Adds behavior to allow sending of a view's selected items, 
    (if they're sendable) around the SendShareItem event. 
    Mixed into the Blocks that have selected items (DetailViewRoot, Table,
    CalendarCanvas).
    
    (At some point, this could be made more generic to support similar
    operations like Printability...)
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
        label = _("Send")
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
                    #label = _("Share")
                #elif 'resharable' in sendStates:
                    #enabled = True
                    #label = _("Send to new")                   
                elif 'sent' in sendStates:
                    # All the items we considered have already been sent.
                    label = _("Sent")
        
        event.arguments['Enable'] = enabled
        event.arguments['Text'] = label

    def onSendShareItemEvent(self, event):
        """ Send or share the selected items """
        selectedItems = self.__getSelectedItems()
        if len(selectedItems) == 0:
            return

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not sharing.ensureAccountSetUp(self.itsView):
            return

        sendableItems = [ item for item in selectedItems 
                          if self.__getSendabilityOf(item) == 'sendable' ]
        assert list(selectedItems) == sendableItems
        for item in sendableItems:
            # For now, make sure we've got a 'from' string.
            # @@@ BJS: this'll go away when we change 'from' to an
            # account picker popup.
            if isinstance (item, Mail.MailMessageMixin):
                if item.ItemWhoFromString() == '':
                    item.whoFrom = item.getCurrentMeEmailAddress()
            item.shareSend()
