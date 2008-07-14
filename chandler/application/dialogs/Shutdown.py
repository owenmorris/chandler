import wx
import wx.html
from osaf.framework.blocks.Styles import getFont
from i18n import ChandlerMessageFactory as _
from osaf.activity import *
import threading
from application import schema
from datetime import datetime, timedelta

class ShutdownDialog(wx.Dialog):
    _cancelled = False
    DEFAULT_STYLE = wx.DOUBLE_BORDER if wx.Platform == '__WXGTK__' else wx.SIMPLE_BORDER
    
    def __init__(self, *args, **kw):
        kw.setdefault('style', self.DEFAULT_STYLE)
        
        self.view = kw.pop('rv', None)
        showCheckbox = kw.pop('showCheckbox', True)

        super(ShutdownDialog, self).__init__(*args, **kw)
        
        logo = wx.GetApp().GetImage("Chandler_64.png")
        bitmap = wx.StaticBitmap(self, -1, logo)

        title = wx.StaticText(self, -1, _(u"Chandler is shutting down..."))
        title.Font = getFont(size=15.0, weight=wx.FONTWEIGHT_BOLD)
        
        self.status = wx.StaticText(self, -1, " ")
        self.status.Font = getFont(size=12.0)
        
        note = wx.html.HtmlWindow(self, -1,
                             style=wx.html.HW_SCROLLBAR_NEVER|wx.html.HW_NO_SELECTION,
                             size=(270, -1))
        note.SetFonts("", "", sizes=[9, 10, 11, 12, 13, 14, 15])
        noteTxt = _(u"NOTE: ")
        warningTxt = _(u"Back up may lose data if\nChandler does not quit completely.")
        
        def fixText(text):
            return text.replace(
                        u"&", u"&amp;"
                    ).replace(
                        u"<", u"&lt;"
                    ).replace(
                        u">", u"&gt;"
                    ).replace(
                        "\n", "<br>"
                    )

        noteHtml = ''.join((
            '<html>\n<body><b><font size="-1">',
            fixText(noteTxt),
            '</font></b>',
            fixText(warningTxt),
            '</body></html>'
        ))

        note.SetPage(noteHtml)
        ir = note.GetInternalRepresentation()
        note.SetSize((ir.GetWidth(), ir.GetHeight()))
        

        if not showCheckbox:
            checkbox = self.cancel = None
        else:
            doBackup = getattr(self._prefs, 'backupOnQuit', True)
            checkbox = wx.CheckBox(self, -1,
                                   _(u"&Back up data when quitting Chandler"))
            checkbox.Font = getFont(size=11.0)
            checkbox.Value = doBackup
            checkbox.SetFocus()
            
            self.cancel = wx.Button(self, wx.ID_CANCEL, _(u"&Skip Back up"))
            self.cancel.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
            self.cancel.Enabled = doBackup
            
            checkbox.Bind(wx.EVT_CHECKBOX, self.OnCheck)
            self.cancel.Bind(wx.EVT_BUTTON, self.OnSkipBackup)
        
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(bitmap, 0, wx.ALIGN_TOP|wx.TOP|wx.LEFT|wx.RIGHT, 20)
        
        topRightSizer = wx.BoxSizer(wx.VERTICAL)
        topRightSizer.Add(title, 0, wx.ALIGN_LEFT|wx.TOP|wx.BOTTOM|wx.RIGHT,
                          40.0)
        topRightSizer.Add(self.status, 0, wx.EXPAND, wx.TOP, 12)
        topRightSizer.Add(note, 0, wx.ALIGN_LEFT|wx.LEFT, -10)
        
        topSizer.Add(topRightSizer, 0, wx.EXPAND|wx.BOTTOM, 30)

        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        if checkbox is not None:
            bottomSizer.Add(checkbox, 1, wx.ALIGN_BOTTOM, 0)
        if self.cancel is not None:
            bottomSizer.Add(self.cancel, 0, wx.ALIGN_BOTTOM |wx.LEFT, 40)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(topSizer, 0, wx.ALIGN_LEFT|wx.ALIGN_TOP, 0)
        self.Sizer.Add(bottomSizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 15)
        
        self.SetAutoLayout(True)
        self.Sizer.Fit(self)

        self.CenterOnScreen()
        self.SetBackgroundColour(wx.WHITE)
        self.status.MinSize = (self.Size.width, self.status.MinSize.height)
       
    def update(self, *args, **kwds):
        # Must be called in main thread

        if 'status' in kwds:
            status = kwds['status']
            if status in (STATUS_ABORTED, STATUS_FAILED, STATUS_COMPLETE):
                if self.cancel is not None:
                    self.cancel.Enabled = False
                return

        if 'msg' in kwds:
            self.status.SetLabel(kwds['msg'])

        wx.GetApp().Yield(True)

    @property
    def _prefs(self):
        if self.view is not None:
            return schema.ns('osaf.app', self.view).prefs
        else:
            return None

    def OnSkipBackup(self, event):
        self.cancel.Enabled = False
        self._cancelled = True

    def OnCheck(self, event):
        prefs = self._prefs
        
        if prefs is not None:
            prefs.backupOnQuit = event.EventObject.Value
            prefs.itsView.commit()

        event.Skip()

    def Process(self, message, f, *args, **kwds):
        """
        Display a status message, and then invoke a callable (with
        args/keywords).
        
        @param message: The message you want the dialog to display
        @type message: C{basestr}
        
        @param f: The function you want called. Args and keywords for f follow
                  f in the Process method call.
        @type f: C{callable}
        """
        self.update(msg=message)
        f(*args, **kwds)

    def _callback(self, activity, *args, **kwds):
        # Can be called from any thread; will call _callback in main thread

        if threading.currentThread().getName() != "MainThread":
            wx.GetApp().PostAsyncEvent(self.update, *args, **kwds)
        else:
            self.update(*args, **kwds)

        return self._cancelled

    def RunBackup(self, backupPath):
        """
        Dump the user's data to backupPath.
        """
        message = _(u"Backing up data...")
        self.update(msg=message)
        
        activity = Activity(message)
        listener = Listener(activity=activity, callback=self._callback)

        Block = schema.ns("osaf.framework.blocks.Block", self.view).Block
        mainView = Block.findBlockByName("MainView")
        mainView.exportToChex(activity, backupPath)

        # note that backup was successful
        restorePrefs = schema.ns("osaf.app", self.view).autoRestorePrefs
        restorePrefs.uptodateBackup = True
        if restorePrefs.enabled and not restorePrefs.hasLocalAttributeValue('nextRestore'):
            restorePrefs.nextRestore = datetime.now() + timedelta(days=7)


if __name__ == "__main__":
    class TestApp(wx.App):
        def GetImage(self, name):
            from i18n import getImage
            import cStringIO
            
            f = getImage(name)
            
            raw = wx.ImageFromStream(cStringIO.StringIO(f.read())).Copy()
            return wx.BitmapFromImage(raw)

        def OnInit(self):
            dialog = ShutdownDialog(None, -1)
            dialog.update(msg="Backing up 37 of 43075 items...") 
            result = dialog.ShowModal()
            dialog.Destroy()
            return False

    app = TestApp(0)
    app.MainLoop()


