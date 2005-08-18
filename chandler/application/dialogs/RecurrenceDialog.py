#Boa:Dialog:RecurrenceDialog

import wx
from wx.lib.anchors import LayoutAnchors
from i18n import OSAFMessageFactory as _

def create(parent):
    return RecurrenceDialog(parent)

[wxID_RECURRENCEDIALOG, wxID_RECURRENCEDIALOGALLBUTTON, 
 wxID_RECURRENCEDIALOGCANCELBUTTON, wxID_RECURRENCEDIALOGFUTUREBUTTON, 
 wxID_RECURRENCEDIALOGQUESTIONTEXT, wxID_RECURRENCEDIALOGTHISBUTTON, 
] = [wx.NewId() for _init_ctrls in range(6)]

class RecurrenceDialog(wx.Dialog):
    def _init_coll_buttonSizer_Items(self, parent):
        # generated method, don't edit

        parent.AddWindow(self.cancelButton, 2, border=5, flag=wx.ALL)
        parent.AddSpacer(wx.Size(50, 10), border=0, flag=0)
        parent.AddWindow(self.allButton, 0, border=5, flag=wx.ALL)
        parent.AddWindow(self.futureButton, 0, border=5, flag=wx.ALL)
        parent.AddWindow(self.thisButton, 0, border=5, flag=wx.ALL)

    def _init_coll_verticalSizer_Items(self, parent):
        # generated method, don't edit

        parent.AddWindow(self.questionText, 1, border=10,
              flag=wx.ADJUST_MINSIZE | wx.ALL)
        parent.AddSizer(self.buttonSizer, 1, border=10,
              flag=wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM)

    def _init_sizers(self):
        # generated method, don't edit
        self.verticalSizer = wx.BoxSizer(orient=wx.VERTICAL)

        self.buttonSizer = wx.FlexGridSizer(cols=0, hgap=0, rows=1, vgap=0)

        self._init_coll_verticalSizer_Items(self.verticalSizer)
        self._init_coll_buttonSizer_Items(self.buttonSizer)

        self.SetSizer(self.verticalSizer)

    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_RECURRENCEDIALOG,
              name=u'RecurrenceDialog', parent=prnt, pos=wx.Point(533, 294),
              size=wx.Size(443, 121),
              style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
              title=_('Recurring event change').toUnicode())
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
        labels = {self.cancelButton : _('Cancel'),
                  self.allButton    : _('All events'),
                  self.futureButton : _('All future events'),
                  self.thisButton   : _('Just this event')}

        for item, label in labels.iteritems():
            item.SetLabel(label.toUnicode())

        # XXX [i18n] Fixme, how should this be localized?
        verb = proxy.changeBuffer[0][0]

        txt = _('"%s" is a recurring event. Do you want to %s:' ) % (proxy.displayName, verb)
        title = _('Recurring event change')

        self.questionText.SetLabel(unicode(text))

        self.SetTitle(unicode(title))

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
