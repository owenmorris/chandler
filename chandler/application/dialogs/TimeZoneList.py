import wx
from i18n import OSAFMessageFactory as _
from application import schema
import itertools

#import application.Globals as Globals
from osaf.pim.calendar.TimeZone import TimeZoneInfo, coerceTimeZone

def pickTimeZone():
    dlg = TimeZoneChooser()
    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
        #for key, btn in dlg.options.iteritems():
            #options[key] = btn.IsChecked()        
        
        dlg.Destroy()
        return None
    else:
        dlg.Destroy()
        return None
      
class TimeZoneChooser(wx.Dialog):
    def __init__(self):

        title = _(u"Choose timezones that should be listed")
        wx.Dialog.__init__(self, id=-1, name=u'TimeZoneChooser',
                           parent=wx.GetApp().mainFrame,
                           style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
                           title=title)

        sizer = wx.BoxSizer(wx.VERTICAL)
       
        buttonSizer = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
                
        self.box = box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer)
        box.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(box)
        box.Fit(self)

        self.Layout()
        self.CenterOnScreen()
import wx
from i18n import OSAFMessageFactory as _
from application import schema
import itertools

#import application.Globals as Globals
from osaf.pim.calendar.TimeZone import TimeZoneInfo, coerceTimeZone

def pickTimeZone():
    dlg = TimeZoneChooser()
    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
        #for key, btn in dlg.options.iteritems():
            #options[key] = btn.IsChecked()        
        
        dlg.Destroy()
        return None
    else:
        dlg.Destroy()
        return None
      
class TimeZoneChooser(wx.Dialog):
    def __init__(self):

        title = _(u"Choose timezones that should be listed")
        wx.Dialog.__init__(self, id=-1, name=u'TimeZoneChooser',
                           parent=wx.GetApp().mainFrame,
                           style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
                           title=title)

        sizer = wx.BoxSizer(wx.VERTICAL)
       
        buttonSizer = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
                
        self.box = box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer)
        box.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(box)
        box.Fit(self)

        self.Layout()
        self.CenterOnScreen()