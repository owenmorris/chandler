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
from osaf.pim.structs import ColorType
from osaf.pim import ContentCollection

from i18n import ChandlerMessageFactory as _

import colorsys
from application import styles

# These colors are duplicated from application/styles.conf so gettext knows they
# need to be localized.
(_(u'Blue'), _(u'Green'), _(u'Red'), _(u'Orange'), _(u'Gold'), _(u'Plum'), 
 _(u'Turquoise'), _(u'Fuchsia'), _(u'Indigo'))

# Collection colors in the form ('Name', localizedName, 360-degree based hue)
order = [s.strip() for s in styles.cfg.get('colororder', 'order').split(',')]
# Using localize instead of "_". The gettext API only parses literal string
# tokens such as _("MyString") when creating pot localization templates, using
# a different function keeps it from complaining
localize = _
collectionHues = [(k, localize(unicode(k)), styles.cfg.getint('colors', k))
                  for k in order]

class CollectionColors(schema.Item):
    """
    Temporarily put the CollectionColors here until we refactor collection
    to remove display information
    """
    colors           = schema.Sequence (ColorType)
    colorIndex       = schema.One (schema.Integer)

    def nextColor (self):
        color = self.colors [self.colorIndex]
        self.colorIndex += 1
        if self.colorIndex == len (self.colors):
            self.colorIndex = 0
        return color

class UserCollection(schema.Annotation):
    schema.kindInfo(annotates=ContentCollection)
    
    renameable               = schema.One(schema.Boolean, defaultValue = True)
    color                    = schema.One(ColorType)
    iconName                 = schema.One(schema.Text, defaultValue = "")
    colorizeIcon             = schema.One(schema.Boolean, defaultValue = True)
    dontDisplayAsCalendar    = schema.One(schema.Boolean, defaultValue = False)
    outOfTheBoxCollection    = schema.One(schema.Boolean, defaultValue = False)
    canAdd                   = schema.One(schema.Boolean, defaultValue = True)
    allowOverlay             = schema.One(schema.Boolean, defaultValue = True)
    searchMatches            = schema.One(schema.Integer, defaultValue = 0)
    checked                  = schema.One(schema.Boolean, defaultValue=False)
    """
      preferredClass is used as a hint to the user-interface to choose the right
      view for the display, e.g. CalendarView for collections that have a
      preferredClass of EventStamp.
    """
    preferredClass           = schema.One(schema.Class)

    schema.addClouds(
        copying = schema.Cloud(byRef=[preferredClass]),
    )

    def ensureColor(self):
        """
        Make sure the collection has a color. Pick up the next color in a predefined 
        list if none was set.
        """
        if not hasattr (self, 'color'):
            self.color = schema.ns('osaf.usercollections', self.itsItem.itsView).collectionColors.nextColor()
        return self
    
    def setColor(self,colorname):
        """
        Set the collection color by name. Raises an error if colorname doesn't exist.
        """
        hue = None
        for colname, coltitle, colhue in collectionHues:
            if colname == colorname:
                hue = colhue
                break
        if hue is None:
            raise ValueError("Unknown color name")
        rgb = colorsys.hsv_to_rgb(hue/360.0,0.5,1.0)
        self.color = ColorType( int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255), 255)

    def setValues(self, **kwds):

        for attr,value in kwds.iteritems():
            setattr(self, attr, value)

def installParcel(parcel, oldVersion=None):

    collectionColors = CollectionColors.update(parcel, 'collectionColors',
        colors = [],
        colorIndex = 0
    )

    for shortName, title, hue in collectionHues:
        rgb = colorsys.hsv_to_rgb(hue/360.0, 0.5, 1.0)
        ct = ColorType(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255), 255)
        collectionColors.colors.append(ct)

    # setup up defaults for well-known parcels
    pim_ns = schema.ns('osaf.pim', parcel.itsView)

    allUC = UserCollection(pim_ns.allCollection)
    allUC.setValues(renameable=False,
                    outOfTheBoxCollection = True,
                    iconName = "Dashboard",
                    colorizeIcon = False,
                    dontDisplayAsCalendar = True,
                    allowOverlay = False)
    allUC.setColor(u'Gold')
                                                   
    trashUC = UserCollection(pim_ns.trashCollection)
    trashUC.setValues(renameable=False,
                      outOfTheBoxCollection = True,
                      iconName = "Trash",
                      colorizeIcon = False,
                      allowOverlay = False,
                      dontDisplayAsCalendar = True,
                      canAdd=False)
    trashUC.setColor(u'Fuchsia')

    inUC = UserCollection(pim_ns.inCollection)
    inUC.setValues(renameable = False,
                   outOfTheBoxCollection = True,
                   iconName = "In",
                   dontDisplayAsCalendar = True,
                   colorizeIcon = False,
                   allowOverlay = False)

    outUC = UserCollection(pim_ns.outCollection)
    outUC.setValues(renameable = False,
                    outOfTheBoxCollection = True,
                    iconName = "Out",
                    colorizeIcon = False,
                    dontDisplayAsCalendar = True,
                    allowOverlay = False)
    

        
