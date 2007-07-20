#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from osaf import Preferences
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
    def __setup__(self):
        # persistent prefs ok in __setup__ because __setup__ is only
        # called when the object is created (or its type is changed),
        # not when it gets restored from the repository
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

class CalendarHourMode(schema.Enumeration):
    values="visibleHours", "pixelSize", "auto"

class CalendarPrefs(Preferences):
    """
    Calendar preferences - there should be a single global instance of
    this object accessible at::

        prefs = schema.ns('osaf.framework.blocks.calendar', view).calendarPrefs
    """
    hourHeightMode = schema.One(CalendarHourMode, defaultValue="visibleHours",
                                doc="Chooses which mode to use when setting "
                                "the hour height.\n"
                                "'visibleHours' means to show exactly the "
                                "number of hours in self.visibleHours\n"
                                "'pixelSize' means it should be exactly the "
                                "pixel size in self.hourPixelSize\n"
                                "'auto' means to base it on the size of the "
                                "font used for drawing")


    visibleHours = schema.One(schema.Integer, defaultValue = 10,
                              doc="Number of hours visible vertically "
                              "when hourHeightMode is 'visibleHours'")
    hourPixelSize = schema.One(schema.Integer, defaultValue = 40,
                               doc="An exact number of pixels for the hour")

    def getHourHeight(self, windowHeight, fontHeight):
        if self.hourHeightMode == "visibleHours":
            return windowHeight/self.visibleHours
        elif self.hourHeightMode == "pixelSize":
            return self.hourPixelSize
        else:
            return (fontHeight+8) * 2
