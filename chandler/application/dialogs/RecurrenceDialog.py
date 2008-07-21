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


#Boa:Dialog:RecurrenceDialog

# RecurrenceDialog's _method methods were created automatically by Boa
# Constructor's GUI designer, but they've been tweaked so it would be tricky
# to edit them again in Boa, so it's OK to edit the generated methods.

import wx
from i18n import ChandlerMessageFactory as _
import logging
from application import schema
from osaf.pim import *
from osaf.pim.mail import MailStamp, getCurrentMeEmailAddresses

logger = logging.getLogger(__name__)

class RecurrenceDialog(wx.Dialog):
    def _init_coll_buttonSizer_Items(self, parent):
        # generated method

        parent.AddWindow(self.cancelButton, 2, border=5, flag=wx.ALL)
        parent.AddSpacer(wx.Size(50, 10), border=0, flag=0)
        parent.AddWindow(self.allButton, 0, border=5, flag=wx.ALL)
        parent.AddWindow(self.futureButton, 0, border=5, flag=wx.ALL)
        parent.AddWindow(self.thisButton, 0, border=5, flag=wx.ALL)

    def _init_coll_verticalSizer_Items(self, parent):
        # generated method

        parent.AddWindow(self.questionText, 1, border=10,
              flag=wx.ADJUST_MINSIZE | wx.ALIGN_LEFT | wx.ALL)
        parent.AddSizer(self.buttonSizer, 0, border=10,
              flag=wx.ALIGN_CENTER_HORIZONTAL | wx.LEFT | wx.RIGHT | wx.BOTTOM)

    def _init_sizers(self):
        # generated method
        self.verticalSizer = wx.BoxSizer(orient=wx.VERTICAL)

        self.buttonSizer = wx.FlexGridSizer(cols=0, hgap=0, rows=1, vgap=0)

        self._init_coll_verticalSizer_Items(self.verticalSizer)
        self._init_coll_buttonSizer_Items(self.buttonSizer)

        self.SetSizer(self.verticalSizer)
        self.SetAutoLayout(True)
        self.verticalSizer.Fit(self)

    def _init_ctrls(self):
        # generated method
        wx.Dialog.__init__(self, id=-1,
              name=u'RecurrenceDialog', parent=None, pos=wx.Point(533, 294),
              size=wx.Size(443, 121),
              style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
              title=_(u'Recurring Event Change'))
        self.SetMinSize(wx.Size(400, 100))
        self.SetClientSize(wx.Size(435, 87))
        self.Bind(wx.EVT_CLOSE, self.onCancel)

        self.cancelButton = wx.Button(id=wx.ID_CANCEL,
              name=u'cancelButton', parent=self)
        self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)

        self.allButton = wx.Button(id=-1, label=u'',
              name='allButton', parent=self)
        self.allButton.Bind(wx.EVT_BUTTON, self.onAll,
              id=-1)

        self.futureButton = wx.Button(id=-1, label=u'',
              name='futureButton', parent=self)
        self.futureButton.Bind(wx.EVT_BUTTON, self.onFuture,
              id=-1)

        self.thisButton = wx.Button(id=-1,
              label=u'', name='thisButton', parent=self)
        self.thisButton.Bind(wx.EVT_BUTTON, self.onThis,
              id=-1)

        self.questionText = wx.StaticText(id=-1,
              label=u'', name=u'questionText', parent=self)

        labels = {self.allButton    : _(u'&All Events'),
                  self.futureButton : _(u'&Future Events'),
                  self.thisButton   : _(u'&This Event')}

        for item, label in labels.iteritems():
            item.SetLabel(label)
 

        self._init_sizers()

    def __init__(self, proxy, question, disabledButtons=()):
        self.proxy = proxy
        self._init_ctrls()

        # use the first action to determine the UI
        self.questionText.SetLabel(question)
        self.questionText.Wrap(sum(self.buttonSizer.GetColWidths()))
        self.SetTitle(_(u'Recurring Event Change'))

        for buttonName in disabledButtons:
            button = getattr(self, buttonName + 'Button')
            button.Enable(False)

        self.Fit()
        self.Layout()
        self.CenterOnScreen()
        self.Show()

    def _accept(self):
        for method, args, kwargs in self.proxy.acceptCallbacks:
            method(*args, **kwargs)
        self.proxy.acceptCallbacks = []
        self._end()

    def _end(self):
        self.proxy.dialogUp = False
        # reset the proxy not to be changing anything
        self.proxy.cancel()

        # Propagate synchronous notification required to
        # update widgets before the screen is readrawn.
        wx.GetApp().propagateAsynchronousNotifications()

        self.Destroy()

    def onCancel(self, event):
        self.proxy.cancel()
        for method in self.proxy.cancelCallbacks:
            method()
        self.proxy.acceptCallbacks = []
        self._end()

    def onAll(self, event):
        self.updateSelection()
        self.proxy.changing = CHANGE_ALL
        self.proxy.makeChanges()
        self._accept()

    def onFuture(self, event):
        self.updateSelection()
        self.proxy.changing = CHANGE_FUTURE
        self.proxy.makeChanges()
        self._accept()

    def onThis(self, event):
        self.updateSelection()
        self.proxy.changing = CHANGE_THIS
        self.proxy.makeChanges()
        self._accept()

    def updateSelection(self):
        view = self.proxy.proxiedItem.itsView
        for change in self.proxy.changes:
            changeType = change[1]
            if (changeType == 'remove' or 
                (changeType == 'add' and 
                 change[2] is schema.ns("osaf.pim", view).trashCollection)):
                from osaf.framework.blocks import Block
                bpb = Block.Block.findBlockByName("SidebarBranchPoint")
                if bpb is not None:
                    view = bpb.childBlocks.first()
                    view.postEventByName("SelectItemsBroadcast", {'items':[]})
                break

_proxies = {}

def getProxy(context, obj, createNew=True, cancelCallback=None):
    """Return a proxy for obj, reusing cached proxies in the same context.

    Return obj if obj doesn't support the changeThis and changeThisAndFuture
    interface.

    In a given context, getting a proxy for a different object removes the
    reference to the old proxy, which should end its life.

    If createNew is False, never create a new proxy, return obj unless there
    is already a cached proxy for obj.

    """
    obj = Stamp(obj).itsItem
    if (not _proxies.has_key(context) or
        _proxies[context][0] != obj.itsUUID):
        if createNew:
            logger.info('creating proxy in context: %s, for uuid: %s' % (context, obj.itsUUID))
            proxy = ChandlerProxy(obj)
            _proxies[context] = (obj.itsUUID, proxy)
        else:
            proxy = obj
    else:
        # We've already got a proxy for this item - we'll reuse it.
        proxy = _proxies[context][1]

        # [Bug 7034]
        # It's possible for proxiedItem to have gone stale; this
        # happens sometimes in Tinderbox testing, where a collection
        # is deleted and re-subscribed to (since Cloud XML sharing
        # preserves UUIDs).
        if proxy.proxiedItem.isStale():
            proxy.proxiedItem = obj

    # sometimes a cancel requires that some UI element needs to
    # be "reset" to the original state.. so queue up the cancel changes
    if (cancelCallback is not None and
        cancelCallback not in proxy.cancelCallbacks):
        proxy.cancelCallbacks.append(cancelCallback)
    return proxy

REMOVE_ALL_MSG = _(u"\"%(displayName)s\" is a recurring event. Changing the occurrence rule to 'Once' will delete all occurrences except for the first one. Do you want to change:")

class ChandlerProxy(RecurrenceProxy):
    _editingProxy = None

    def __init__(self, item):
        super(ChandlerProxy, self).__init__(item)
        self.dialogUp = False
        self.cancelCallbacks = []
        self.acceptCallbacks = []

    def beginSession(self):
        type(self)._editingProxy = self

    def endSession(self):
        # @@@ [grant] Need to think about this!
        if self == type(self)._editingProxy:
            type(self)._editingProxy = None
            item = self.proxiedItem

            if not isDead(item) and has_stamp(item, EventStamp):
                item = EventStamp(item).getMaster().itsItem

            if (item is not None and not
                item.hasLocalAttributeValue('lastModification')):
                item.changeEditState(Modification.created, who=item.lastModifiedBy)

    def addToCollection(self, collection):
        """
        Add self to the given collection, or queue the add.
        """
        trash = schema.ns("osaf.pim", collection.itsView).trashCollection
        itemInTrash = collection is not trash and trash in self.collections
        
        if itemInTrash or not collection in self.collections:
            self.collections.add(collection)
            if itemInTrash:
                self.collections.remove(trash)

    def removeFromCollection(self, collection, cutting=False):
        """
        Remove self from the given collection, or queue the removal.

        [@@@] grant: Need to handle 'cutting' case.
        """
        self._prepareToRemoveFromCollection(collection)
        self.collections.remove(collection)

    def appendChange(self, *args):
        # Short-circuit adding the MailStamp to change all events,
        # no matter what.
        if args[1] in ('addStamp', 'removeStamp'):
            if args[2].stamp_type == MailStamp:
                allChange = CHANGE_ALL(MailStamp(self.proxiedItem))
                if args[1] == 'addStamp':
                    allChange.add()
                else:
                    allChange.remove()
                return

        super(ChandlerProxy, self).appendChange(*args)

        if self.changes and not self.dialogUp:
            # [Bug 4110] Put the dialog on-screen asynchronously
            # This code can get called while wx is busy changing
            # focus, etc, and popping a new window onscreen seems
            # to get it into a weird state.
            self.dialogUp = True
            wx.GetApp().PostAsyncEvent(self.runDialog)

    def runDialog(self):
        # Check in case the dialog somehow got cancelled
        if self.dialogUp:

            questionFmt = None
            disabled = set()

            # use the last change to determine which text to use, since removal
            # from a collection may first add the item to the dashboard
            change = self.changes[-1]
            changeType = change[1]

            if changeType == 'addStamp':
                stampClass = change[2].schemaItem.stampClass
                if stampClass == TaskStamp:
                    questionFmt = _(u'"%(displayName)s" is a recurring event. Do you want to add to the Task list:')
            elif changeType == 'removeStamp':
                stampClass = change[2].schemaItem.stampClass
                if stampClass == TaskStamp:
                    questionFmt = _(u'"%(displayName)s" is a recurring event. Do you want to remove from the Task list:')
                elif stampClass == EventStamp:
                    questionFmt = _(u'"%(displayName)s" is a recurring event. Removing it from the Calendar will remove all occurrences. Do you want to remove:')
                    disabled.update(('future', 'this'))
            elif changeType == 'add':
                trash = schema.ns("osaf.pim", self.proxiedItem.itsView).trashCollection

                if change[2] is trash:
                      questionFmt=_(u'"%(displayName)s" is a recurring event. Do you want to delete:')
                else:
                    questionFmt = _(u'"%(displayName)s" is a recurring event. Do you want to add:')
                    disabled.update(('future', 'this'))
            elif changeType == 'remove':
                questionFmt=_(u'"%(displayName)s" is a recurring event. Do you want to remove:')
                disabled.update(('future', 'this'))
            elif changeType == 'set':
                if change[2] == EventStamp.rruleset.name:
                    disabled.update(('this',))
                    if change[3] is None:
                        questionFmt = REMOVE_ALL_MSG
                    else:
                        questionFmt = _(u"\"%(displayName)s\" is a recurring event. Changing the occurrence rule may cause some events to be deleted. Do you want to change:")
            elif changeType == 'delete':
                if change[2] == EventStamp.rruleset.name:
                    questionFmt = REMOVE_ALL_MSG
                    disabled.update(('future', 'this'))

            if questionFmt is None:
                questionFmt = _(u'"%(displayName)s" is a recurring event. Do you want to change:')

            master = EventStamp(self.proxiedItem).getMaster()
            event = EventStamp(self.proxiedItem)

            if event in (master, master.getFirstOccurrence()):
                disabled.add('future')

            RecurrenceDialog(
                self, questionFmt % { 'displayName' : self.displayName },
                disabled)

    def getMembershipItem(self):
        """
        When testing an item for membership, what we generally care
        about is the master event, unless the item is a modification.
        """
        event = EventStamp(self.proxiedItem)
        if event.modificationFor is not None:
            # modifications should be their own membership item
            return event.itsItem
        else:
            return event.getMaster().itsItem.getMembershipItem()

def delayForRecurrenceDialog(item, callback, *args, **kwargs):
    """
    If the given item has a current UI proxy with changes, delay calling
    callback(*args, **kwargs) until the recurrence dialog is answered
    positively.
    
    If the recurrence dialog is cancelled, the callback will never be called.
    
    Identical callbacks won't be queued more than once.
    
    Block.finishEdits() should be called before delayForRecurrenceDialog, or
    the proxy may not see changes about to be set by edited widgets.
    
    """
    proxy = getProxy('ui', item, createNew=False)
    if proxy.isProxy and proxy.changes:
        for function, a, k in proxy.acceptCallbacks:
            if callback == function:
                break
        else:
            proxy.acceptCallbacks.append((callback, args, kwargs))
    else:
        callback(*args, **kwargs)
