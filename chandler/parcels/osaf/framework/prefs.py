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


from application import schema

"""
Here's how you should use the Preferences class:

Declare a new pref class
------------------------

from osaf.app import Preferences
class MyPrefs(Preferences):
    textPref = schema.One(schema.Text, defaultValue='somevalue')

then install it in your module:

def installParcel(parcel, ...):
    MyPrefs.update(parcel, 'MyPrefs')

Accessing a preference
----------------------

myPrefs = schema.ns("my.module.namespace", view).MyPrefs
prefValue = myPrefs.textPref

To iterate all preferences you'd just say:

for parcelPref in Preferences.iterItems(view):
    print "In pref object %s:" % parcelPref.__class__.__name__
    for prefname, prefvalue, preftype in prefObj.iterAttributes():
        print "    %s=%s" % (prefname, prefvalue)

Watching for changes
--------------------

class SomeObject(schema.Item):
    def __init__(self, *args, **kwds):
        # persistent prefs ok in __init__ because __init__ is only
        # called the first time the object is created, not when it
        # gets restored from the repository
        self.watchItem(myPrefs, 'onMyPrefChanged')

    def onMyPrefChanged(self, op, pref, names):
        if 'textPref' in names:
            print "textPref just changed to %s" % pref.textPref

"""

class Preferences(schema.Item):
    """
    base class for any and all preferences
    """
    pass
