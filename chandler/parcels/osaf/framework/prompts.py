
import wx
from application import schema
from osaf.framework import Preferences
from application.dialogs.Util import ShowMessageDialog
from i18n import OSAFMessageFactory as _

class DialogPref(Preferences):
    """
    A preference class to use for pop-up dialogs

    if response is not defined, then the response will be 'None'
    """
    response = schema.One(schema.Boolean)
    askNextTime = schema.One(schema.Boolean, defaultValue=True)


def prefPrompt(message, pref, flags, parent=None, resultsTable=None, caption=None):
    if pref is not None and not pref.askNextTime:
        if pref.hasLocalAttributeValue('response'):
            return pref.response
        else:
            return None
    
    if parent is None:
        parent = wx.GetApp().mainFrame

    if caption is None:
        caption = _(u"Chandler")

    return ShowMessageDialog(parent, message, caption, flags, resultsTable)


def promptYesNo(message, pref=None, parent=None, caption=None):

    return prefPrompt(message, pref, 
                      wx.YES_NO,
                      parent=parent,
                      resultsTable={wx.ID_YES: True,
                                    wx.ID_NO: False},
                      caption=caption)

def promptYesNoCancel(message, pref=None, parent=None, caption=None):
    
    return prefPrompt(message, pref,
                      wx.YES_NO | wx.CANCEL,
                      parent=parent,
                      resultsTable={wx.ID_YES: True,
                                    wx.ID_NO: False,
                                    wx.ID_CANCEL: None },
                      caption=caption)
                       
def promptOk(message, pref=None, parent=None, caption=None):

    return prefPrompt(message, pref, wx.OK, parent=parent, caption=caption)
