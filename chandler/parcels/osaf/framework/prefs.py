
from application import schema

"""
Here's how you should use the Preferences class:

from osaf.app import Preferences
class MyPrefs(Preferences):
    textPref = schema.One(schema.Text, defaultValue='somevalue')

then install it in your module:

def installParcel(parcel, ...):
    MyPrefs.update(parcel, 'MyPrefs')

now to access your preferences you'd say

myPrefs = schema.ns("my.module.namespace", view).MyPrefs
prefValue = myPrefs.textPref

To iterate all preferences you'd just say:

for parcelPref in Preferences.iterItems(view):
    print "In pref object %s:" % parcelPref.__class__.__name__
    for prefname, prefvalue, preftype in prefObj.iterAttributes():
        print "    %s=%s" % (prefname, prefvalue)

"""

class Preferences(schema.Item):
    """
    base class for any and all preferences
    """
    pass
