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


import wx
from application import schema
from osaf import Preferences

from application.dialogs.Util import ShowMessageDialog
from i18n import ChandlerMessageFactory as _

class DialogPref(Preferences):
    """
    A preference class to use for pop-up dialogs

    if response is not defined, then the response will be 'None'
    """
    response = schema.One(schema.Boolean)
    askNextTime = schema.One(schema.Boolean, defaultValue=True)


def prefPrompt(message, pref, flags, resultsTable=None,
               caption=None, textTable=None):
    if pref is not None and not pref.askNextTime:
        if pref.hasLocalAttributeValue('response'):
            return pref.response
        else:
            return None
    
    if caption is None:
        caption = _(u"Chandler")

    return ShowMessageDialog(message, caption, flags, resultsTable, textTable)


def promptYesNo(message, pref=None, parent=None, caption=None, textTable=None):

    return prefPrompt(message, pref, 
                      wx.YES_NO,
                      resultsTable={wx.ID_YES: True,
                                    wx.ID_NO: False},
                      caption=caption,
                      textTable=textTable)

def promptYesNoCancel(message, pref=None, parent=None, caption=None,
                      textTable=None):
    
    return prefPrompt(message, pref,
                      wx.YES_NO | wx.CANCEL,
                      resultsTable={wx.ID_YES: True,
                                    wx.ID_NO: False,
                                    wx.ID_CANCEL: None },
                      caption=caption,
                      textTable=textTable)

def promptOk(message, pref=None, parent=None, caption=None):

    return prefPrompt(message, pref, wx.OK, caption=caption)
