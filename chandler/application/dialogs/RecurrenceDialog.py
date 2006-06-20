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


#Boa:Dialog:RecurrenceDialog

# RecurrenceDialog's _method methods were created automatically by Boa
# Constructor's GUI designer, but they've been tweaked so it would be tricky
# to edit them again in Boa, so it's OK to edit the generated methods.

import wx
from i18n import OSAFMessageFactory as _
import logging
from application import schema

logger = logging.getLogger(__name__)

def create(parent):
    return RecurrenceDialog(parent)

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
              flag=wx.ADJUST_MINSIZE | wx.ALL)
        parent.AddSizer(self.buttonSizer, 1, border=10,
              flag=wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM)

    def _init_sizers(self):
        # generated method
        self.verticalSizer = wx.BoxSizer(orient=wx.VERTICAL)

        self.buttonSizer = wx.FlexGridSizer(cols=0, hgap=0, rows=1, vgap=0)

        self._init_coll_verticalSizer_Items(self.verticalSizer)
        self._init_coll_buttonSizer_Items(self.buttonSizer)

        self.SetSizer(self.verticalSizer)
        self.SetAutoLayout(True)
        self.verticalSizer.Fit(self)

    def _init_ctrls(self, prnt):
        # generated method
        wx.Dialog.__init__(self, id=-1,
              name=u'RecurrenceDialog', parent=prnt, pos=wx.Point(533, 294),
              size=wx.Size(443, 121),
              style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
              title=_(u'Recurring event change'))
        self.SetMinSize(wx.Size(400, 100))
        self.SetClientSize(wx.Size(435, 87))
        self.Bind(wx.EVT_CLOSE, self.onCancel)

        self.cancelButton = wx.Button(id=wx.ID_CANCEL,
              name=u'cancelButton', parent=self)
        self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancel)

        self.allButton = wx.Button(id=-1, label=u'',
              name=u'allButton', parent=self)
        self.allButton.Bind(wx.EVT_BUTTON, self.onAll,
              id=-1)

        self.futureButton = wx.Button(id=-1, label=u'',
              name=u'futureButton', parent=self)
        self.futureButton.Bind(wx.EVT_BUTTON, self.onFuture,
              id=-1)

        self.thisButton = wx.Button(id=-1,
              label=u'', name=u'thisButton', parent=self)
        self.thisButton.Bind(wx.EVT_BUTTON, self.onThis,
              id=-1)

        self.questionText = wx.StaticText(id=-1,
              label=u'', name=u'questionText', parent=self)

        labels = {self.allButton    : _(u'All events'),
                  self.futureButton : _(u'All future events'),
                  self.thisButton   : _(u'Just this event')}

        for item, label in labels.iteritems():
            item.SetLabel(label)


        self._init_sizers()

    def __init__(self, parent, proxy, endCallbacks):
        self.proxy = proxy
        self.endCallbacks = endCallbacks
        self._init_ctrls(parent)

        # use the first action to determine the UI
        change = proxy.changeBuffer[0]
        question = change['question']
        txt = question % { 'displayName' : proxy.displayName }
        title = _(u'Recurring event change')
        self.questionText.SetLabel(txt)
        self.SetTitle(title)

        for buttonName in change.get('disabled_buttons', []):
            button = getattr(self, buttonName + 'Button')
            button.Enable(False)
        
        self.Fit()
        self.Layout()
        self.CenterOnScreen()
        self.Show()

    def _end(self):
        self.proxy.dialogUp = False
        for method in self.endCallbacks:
            method()

        # Propagate synchronous notification required to
        # update widgets before the screen is readrawn.
        wx.GetApp().propagateAsynchronousNotifications()

        self.Destroy()
        
    def onCancel(self, event):
        self.proxy.cancelBuffer()
        self._end()

    def onAll(self, event):
        self.proxy.currentlyModifying = 'all'
        self.proxy.propagateBufferChanges()
        self._end()

    def onFuture(self, event):
        self.proxy.currentlyModifying = 'thisandfuture'
        self.proxy.propagateBufferChanges()
        self._end()

    def onThis(self, event):
        self.proxy.currentlyModifying = 'this'
        self.proxy.propagateBufferChanges()
        self._end()



_proxies = {}

def getProxy(context, obj, createNew=True, endCallback=None):
    """Return a proxy for obj, reusing cached proxies in the same context.
        
    Return obj if obj doesn't support the changeThis and changeThisAndFuture
    interface.
    
    In a given context, getting a proxy for a different object removes the
    reference to the old proxy, which should end its life.
    
    If createNew is False, never create a new proxy, return obj unless there
    is already a cached proxy for obj.
    
    """
    if hasattr(obj, 'changeThis') and hasattr(obj, 'changeThisAndFuture'):      
        if (not _proxies.has_key(context) or
            _proxies[context][0] != obj.itsUUID):
            if createNew:
                logger.info('creating proxy in context: %s, for uuid: %s' % (context, obj.itsUUID))
                proxy = OccurrenceProxy(obj)
                _proxies[context] = (obj.itsUUID, proxy)
            else:
                return obj
        else:
            # We've already got a proxy for this item - we'll reuse it.
            proxy = _proxies[context][1]
            
            # Before we return it, update its __class__ in case it was stamped
            # since the last time it got used. (see bug 4660)
            proxy.__class__ = obj.__class__

        # sometimes a cancel requires that some UI element needs to
        # be "reset" to the original state.. so queue up the cancel changes
        if (endCallback is not None and
            endCallback not in proxy.endCallbacks):
            proxy.endCallbacks.append(endCallback)
        return proxy
    else:
        return obj

class OccurrenceProxy(object):
    """Proxy which pops up a RecurrenceDialog when it's changed."""
    __class__ = 'temp'
    proxyAttributes = 'proxiedItem', 'currentlyModifying', '__class__', \
                      'dialogUp', 'changeBuffer', 'endCallbacks'
    
    def __init__(self, item):
        self.proxiedItem = item
        self.currentlyModifying = None
        self.__class__ = self.proxiedItem.__class__
        self.dialogUp = False
        self.endCallbacks = []

        # change buffer is an array of dicts, where each dict contains
        # information required to propagate the change
        self.changeBuffer = []
        
    def __ne__(self, other):
        return self.proxiedItem != other

    def __eq__(self, other):
        return self.proxiedItem == other
    
    def __repr__(self):
        return "Proxy for %s" % self.proxiedItem.__repr__()

    def _repr_(self):
        """Temporarily overriding the special repository for representation."""
        return "Proxy for %s" % self.proxiedItem._repr_()

    def __str__(self):
        return "Proxy for %s" % self.proxiedItem.__str__()
        
    def __getattr__(self, name):
        """Get the last name version set in changeBuffer, or get from proxy."""
        for change in reversed(self.changeBuffer):
            if change.get('affects_getattr', False) is False:
                continue
            else:
                (attr, value) = change.get('args')
            if attr == name:
                return value
        return getattr(self.proxiedItem, name)
        
    def __setattr__(self, name, value):
        if name in self.proxyAttributes:
            object.__setattr__(self, name, value)
        elif self.proxiedItem.rruleset is None:
            setattr(self.proxiedItem, name, value)
        else:
            testedEqual = False
            
            #
            # In the case of datetime-valued attributes, we don't want to
            # do == comparison right away, since:
            #
            # (1) it could raise a TypeError if comparing naive and
            #     non-naive values
            #
            # (2) it can return True when we still want to propagate
            #     a change; for example if trying to change the timezone
            #     from your default to floating.
            #
            if hasattr(self.proxiedItem, name):
                oldValue = getattr(self.proxiedItem, name)
                
                # These will be None for non-datetime values
                oldTzinfo = getattr(oldValue, 'tzinfo', None)
                tzinfo = getattr(value, 'tzinfo', None)
                
                # By checking the tzinfos first, we bypass the
                # possible TypeError, too.
                testedEqual = (oldTzinfo == tzinfo and oldValue == value)
                    
            if testedEqual:
                pass
            elif self.currentlyModifying is None:
                change = dict(method=self.propagateChange,
                              args = (name, value),
                              question = _(u'"%(displayName)s" is a recurring event. Do you want to change:'),
                              affects_getattr = True,
                              disabled_buttons=('all',))
                self.delayChange(change)
            else:
                self.propagateChange(name, value)

    def addToCollection(self, collection):
        """
        Add self to the given collection, or queue the add.
        """
        if self.proxiedItem.rruleset is None:
            collection.add(self.proxiedItem.getMaster())
        else:
            trash = schema.ns('osaf.pim',
                self.proxiedItem.itsView).trashCollection
            if collection == trash:
                self.removeFromCollection(collection)
            else:
                change = dict(method=self.propagateAddToCollection,
                              args=(collection,),
                              question = _(u'"%(displayName)s" is a recurring event. What do you want to add to the collection:'),
                              disabled_buttons=('future', 'this'))
    
                self.delayChange(change)
            
    def removeFromCollection(self, collection, cutting = False):
        """
        Remove self from the given collection, or queue the removal.
        """
        if self.proxiedItem.rruleset is None:
            collection.remove(self.proxiedItem.getMaster())
        else:
            change = dict(method=self.propagateDelete,
                          args=(collection,),
                          question=_(u'"%(displayName)s" is a recurring event. Do you want to delete:'))
            if cutting:
                change['question'] = _(u'"%(displayName)s" is a recurring event. Do you want to cut:')
                change['disabled_buttons']=('future', 'this')
            self.delayChange(change)

    def StampKind(self, *args, **kwds):
        """
        We have to make sure to propagate the change to __class__ even on
        non-recurring events.
        
        For recurring events, propagate StampKind()
        """
        if self.proxiedItem.rruleset is None:
            self.proxiedItem.StampKind(*args, **kwds)

            # need to make sure our __class__ matches the newly stamped item
            self.__class__ = self.proxiedItem.__class__
            assert self.__class__ is self.proxiedItem.__class__, "couldn't make the conversion from %s to %s" % (self.__class__.__name__, self.proxiedItem.__class__)
        else:
            change = dict(method=self.propagateStampKind,
                          args = args,
                          kwds = kwds,
                          question = _(u'"%(displayName)s" is a recurring event. Do you want to stamp:'),
                          disabled_buttons=('all','future'))

            self.delayChange(change)

    def delayChange(self, change):
        """
        Given a change dict, queue it up and pop up a dialog if necessary
        """
        self.changeBuffer.append(change)
        if not self.dialogUp:
            # [Bug 4110] Put the dialog on-screen asynchronously
            # This code can get called while wx is busy changing
            # focus, etc, and popping a new window onscreen seems
            # to get it into a weird state.
            self.dialogUp = True
            wx.GetApp().PostAsyncEvent(self.runDialog)
        
    def runDialog(self):
        # Check in case the dialog somehow got cancelled
        if self.dialogUp:
            RecurrenceDialog(wx.GetApp().mainFrame, self, self.endCallbacks)
    
    def propagateBufferChanges(self):
        while len(self.changeBuffer) > 0:
            change = self.changeBuffer.pop(0)

            # unpack the call
            method = change['method']
            args = change.get('args', [])
            kwds = change.get('kwds', {})

            method(*args, **kwds)
            
        if self.currentlyModifying in ('thisandfuture', 'all'):
            self.currentlyModifying = None
    
    def propagateChange(self, name, value):
        table = {'this'          : self.proxiedItem.changeThis,
                 'thisandfuture' : self.proxiedItem.changeThisAndFuture}
        table[self.currentlyModifying](name, value)

    def propagateDelete(self, collection):
        table = {'this'          : self.proxiedItem.deleteThis,
                 'thisandfuture' : self.proxiedItem.deleteThisAndFuture,
                 'all'           : lambda: self.trashAddOrDelete(collection)
                }
        table[self.currentlyModifying]()

    def trashAddOrDelete(self, collection):
        """
        If collection is trash, deletion action was triggered by adding to
        trash, so add self.proxiedItem to trash, which appears to the user as
        removing the item from all collections it was in.
        
        If collection isn't trash, then this was called from a normal delete,
        just remove self.proxiedItem from that collection.

        """
        trash = schema.ns('osaf.pim', self.proxiedItem.itsView).trashCollection
        master = self.proxiedItem.getMaster()
        if collection == trash:
            collection.add(master)
        else:
            collection.remove(master)


    def propagateAddToCollection(self, collection):
        collection.add(self.proxiedItem.getMaster())

    def propagateStampKind(self, *args, **kwds):
        # todo: process currentlyModifying
        self.proxiedItem.changeThis()
        self.proxiedItem.StampKind(*args, **kwds)

    def cancelBuffer(self):
        self.changeBuffer = []
    
    def isProxy(self):
        return True

    def getMembershipItem(self):
        """
        When testing an item for membership, what we generally care
        about is the master event.
        """
        return self.proxiedItem.getMaster().getMembershipItem()
