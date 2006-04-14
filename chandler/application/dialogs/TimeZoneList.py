import wx
from i18n import OSAFMessageFactory as _
from application import schema
import itertools
import PyICU

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
        
TIMEZONE_OTHER_FLAG = -1

def buildTZChoiceList(view, control, selectedTZ=None):
    """
    Take a wx.Choice control and a timezone to select.  Populate the control
    with the appropriate timezones, plus an Other option, whose value is
    TIMEZONE_OTHER_FLAG.

    Default selection is ICUtzinfo.default.
    
    """
    control.Clear()
    selectIndex = -1
    info = TimeZoneInfo.get(view)
    if selectedTZ is None:
        selectedTZ = PyICU.ICUtzinfo.default
    canonicalTimeZone = info.canonicalTimeZone(selectedTZ)

    # rebuild the list of choices
    for name, zone in info.iterTimeZones():
        if canonicalTimeZone == zone:
            selectIndex = control.Append(name, clientData=selectedTZ)
        else:
            control.Append(name, clientData=zone)

    # Always add the Other option
    control.Append(_(u"Other..."),
                   clientData=TIMEZONE_OTHER_FLAG)

    if selectIndex is -1:
        control.Insert(unicode(selectedTZ), 0, clientData=selectedTZ)
        selectIndex = 0
        
    if selectIndex != -1:
        control.Select(selectIndex)
