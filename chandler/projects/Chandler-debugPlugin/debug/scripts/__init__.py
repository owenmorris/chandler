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
import osaf.startup as startup
from osaf.framework import scripting


def installParcel(parcel, oldVersion=None):
    osafDev = schema.ns("osaf.app", parcel.itsView).OSAFContact

    # Script to create a new user script item
    newScript = scripting.Script.update(parcel, 'New Script',
                                        displayName=u"Shift+F1 - Create a new script",
                                        fkey= u"F1",
                                        creator = osafDev,
                                        body=scripting.script_file(u"NewScript.py", __name__)
                                        )

    # Block Inspector
    scripting.Script.update(parcel, 'Block Inspector',
                            displayName=u"Shift+F2 - Block under cursor",
                            fkey= u"F2",
                            creator = osafDev, body=scripting.script_file(u"BlockInspector.py", __name__)
                            )

    # Item Inspector
    scripting.Script.update(parcel, 'Item Inspector',
                            displayName=u"Shift+F3 - Item selected",
                            fkey= u"F3",
                            creator = osafDev,
                            body=scripting.script_file(u"ItemInspector.py", __name__)
                            )

    # Browse selected item
    scripting.Script.update(parcel, 'Browse Selected',
                            displayName=u"Shift+F4 - Browse selected item",
                            fkey= u"F4",
                            creator = osafDev,
                            body=scripting.script_file(u"BrowseSelected.py", __name__)
                            )

    scripting.Script.update(parcel, 'Event Timing',
                            displayName=u"Test - Event timing example",
                            test=True,
                            creator = osafDev,
                            body=scripting.script_file(u"EventTiming.py", __name__)
                            )

    #
    # F5 reserved for triage
    #

    # Print selected item to stdout
    scripting.Script.update(parcel, 'Print Selected to stdout',
                            displayName=u"Shift+F6 - Print selected item to stdout",
                            fkey= u"F6",
                            creator = osafDev,
                            body=scripting.script_file(u"StdoutSelected.py", __name__)
                            )

    # Script to paste the clipboard into a new menu item
    newScript = scripting.Script.update(parcel, 'Paste New Item',
                                        displayName=u"Shift+F7 - Paste new item",
                                        fkey= u"F7",
                                        creator = osafDev,
                                        body=scripting.script_file(u"PasteNewItem.py", __name__)
                                        )

    startup.Startup.update(parcel, "installKeyHandler",
        invoke=__name__ + ".installKeyHandler"
    )

def hotkey_script(event, view):
    """
    Check if the event is a hot key to run a script.
    Returns True if it does trigger a script to run, False otherwise.
    """
    keycode = event.GetKeyCode()
    # for now, we just allow function keys to be hot keys.
    if (wx.WXK_F1 <= keycode <= wx.WXK_F24
            and not event.AltDown()
            and not event.CmdDown()
            and not event.ControlDown()
            and not event.MetaDown()
            and event.ShiftDown()):
        # try to find the corresponding Script
        targetFKey = u"F%(FunctionKeyNumber)s" % {'FunctionKeyNumber':unicode(keycode-wx.WXK_F1+1)}

        # maybe we have an existing script?
        script = _findHotKeyScript(targetFKey, view)
        if script:
            wx.CallAfter(script.execute)
            return

    # not a hot key
    event.Skip()

def _findHotKeyScript(targetFKey, view):
    # find a script that starts with the given name
    for aScript in scripting.Script.iterItems(view):
        if aScript.fkey == targetFKey:
            return aScript
    return None


def installKeyHandler(startup):
    app = wx.GetApp()
    view = startup.itsView
    
    if app is not None:
        app.Bind(wx.EVT_KEY_DOWN, lambda event: hotkey_script(event, view))
