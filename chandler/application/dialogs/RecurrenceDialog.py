#Boa:Dialog:RecurrenceDialog

# RecurrenceDialog's _method methods were created automatically by Boa
# Constructor's GUI designer, but they've been tweaked so it would be tricky
# to edit them again in Boa, so it's OK to edit the generated methods.

import wx
from wx.lib.anchors import LayoutAnchors
from i18n import OSAFMessageFactory as _
from osaf import messages
import logging

logger = logging.getLogger(__name__)

def create(parent):
    return RecurrenceDialog(parent)

[wxID_RECURRENCEDIALOG, wxID_RECURRENCEDIALOGALLBUTTON, 
 wxID_RECURRENCEDIALOGCANCELBUTTON, wxID_RECURRENCEDIALOGFUTUREBUTTON, 
 wxID_RECURRENCEDIALOGQUESTIONTEXT, wxID_RECURRENCEDIALOGTHISBUTTON, 
] = [wx.NewId() for _init_ctrls in range(6)]

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

    def _init_ctrls(self, prnt):
        # generated method
        wx.Dialog.__init__(self, id=wxID_RECURRENCEDIALOG,
              name=u'RecurrenceDialog', parent=prnt, pos=wx.Point(533, 294),
              size=wx.Size(443, 121),
              style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
              title=_(u'Recurring event change'))
        self.SetMinSize(wx.Size(400, 100))
        self.SetClientSize(wx.Size(435, 87))
        self.Bind(wx.EVT_CLOSE, self.onCancel)

        self.cancelButton = wx.Button(id=wxID_RECURRENCEDIALOGCANCELBUTTON,
              label=u'', name=u'cancelButton', parent=self)
        self.cancelButton.Bind(wx.EVT_BUTTON, self.onCancel,
              id=wxID_RECURRENCEDIALOGCANCELBUTTON)

        self.allButton = wx.Button(id=wxID_RECURRENCEDIALOGALLBUTTON, label=u'',
              name=u'allButton', parent=self)
        self.allButton.Bind(wx.EVT_BUTTON, self.onAll,
              id=wxID_RECURRENCEDIALOGALLBUTTON)

        self.futureButton = wx.Button(id=wxID_RECURRENCEDIALOGFUTUREBUTTON,
              label=u'', name=u'futureButton', parent=self)
        self.futureButton.Bind(wx.EVT_BUTTON, self.onFuture,
              id=wxID_RECURRENCEDIALOGFUTUREBUTTON)

        self.thisButton = wx.Button(id=wxID_RECURRENCEDIALOGTHISBUTTON,
              label=u'', name=u'thisButton', parent=self)
        self.thisButton.Bind(wx.EVT_BUTTON, self.onThis,
              id=wxID_RECURRENCEDIALOGTHISBUTTON)

        self.questionText = wx.StaticText(id=wxID_RECURRENCEDIALOGQUESTIONTEXT,
              label=u'', name=u'questionText', parent=self)

        self._init_sizers()

    def __init__(self, parent, proxy):
        self.proxy = proxy
        self._init_ctrls(parent)
        labels = {self.cancelButton : messages.CANCEL,
                  self.allButton    : _(u'All events'),
                  self.futureButton : _(u'All future events'),
                  self.thisButton   : _(u'Just this event')}

        for item, label in labels.iteritems():
            item.SetLabel(label)

        # XXX [i18n] Fixme, how should this be localized?
        verb = proxy.changeBuffer[0][0]

        txt = _(u'"%(displayName)s" is a recurring event. Do you want to %(needsLocalization)s:' ) % \
                                  {'displayName': proxy.displayName, 'needsLocalization': verb}

        title = _(u'Recurring event change')

        self.questionText.SetLabel(txt)

        self.SetTitle(title)

        # Make sure the dialog can fit the buttons and question text
        self.SetSize(self.GetBestSize())

        if verb == 'change': # changes don't apply to all, hide the all button
            self.allButton.Show(False)

        self.CenterOnScreen()
        self.Show()

    def _end(self):
        self.proxy.dialogUp = False
        self.Destroy()

    def onCancel(self, event):
        self.proxy.cancelBuffer()
        self._end()

    def onAll(self, event):
        event.Skip()

    def onFuture(self, event):
        self.proxy.currentlyModifying = 'thisandfuture'
        self.proxy.propagateBufferChanges()
        self._end()

    def onThis(self, event):
        self.proxy.currentlyModifying = 'this'
        self.proxy.propagateBufferChanges()
        self._end()



_proxies = {}

def getProxy(context, obj, createNew=True):
    """Return a proxy for obj, reusing cached proxies in the same context.
        
    Return obj if obj doesn't support the changeThis and changeThisAndFuture
    interface.
    
    In a given context, getting a proxy for a different object removes the
    reference to the old proxy, which should end its life.
    
    If createNew is False, never create a new proxy, return obj unless there
    is already a cached proxy for obj.
    
    """
    if hasattr(obj, 'changeThis') and hasattr(obj, 'changeThisAndFuture'):      
        if not _proxies.has_key(context) or _proxies[context][0] != obj.itsUUID:
            if createNew:
                logger.info('creating proxy in context: %s, for uuid: %s' % (context, obj.itsUUID))
                _proxies[context] = (obj.itsUUID, OccurrenceProxy(obj))
            else:
                return obj
        return _proxies[context][1]
    else:
        return obj

class OccurrenceProxy(object):
    """Proxy which pops up a RecurrenceDialog when it's changed."""
    __class__ = 'temp'
    proxyAttributes = 'proxiedItem', 'currentlyModifying', '__class__', \
                      'dialogUp', 'changeBuffer'
    
    def __init__(self, item):
        self.proxiedItem = item
        self.currentlyModifying = None
        self.__class__ = self.proxiedItem.__class__
        self.dialogUp = False
        self.changeBuffer = []
    
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
        for i, attr, value in reversed(self.changeBuffer):
            if attr == name:
                return value
        return getattr(self.proxiedItem, name)
        
    def __setattr__(self, name, value):
        if name in self.proxyAttributes:
            object.__setattr__(self, name, value)
        elif self.proxiedItem.rruleset is None:
            setattr(self.proxiedItem, name, value)
        else:
            if self.currentlyModifying is None:
                self.changeBuffer.append(('change', name, value))
                if not self.dialogUp:
                    self.dialogUp = True
                    RecurrenceDialog(wx.GetApp().mainFrame, self)
            else:
                self.propagateChange(name, value)
    
    def propagateBufferChanges(self):
        while len(self.changeBuffer) > 0:
            self.propagateChange(*self.changeBuffer.pop(0)[1:])
    
    def propagateChange(self, name, value):
        table = {'this'          : self.changeThis,
                 'thisandfuture' : self.changeThisAndFuture}
        table[self.currentlyModifying](name, value)
    
    def cancelBuffer(self):
        self.changeBuffer = []
    
    def isProxy(self):
        return True

