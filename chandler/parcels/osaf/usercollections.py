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


from osaf.pim.structs import ColorType

from application import schema
from osaf.pim.structs import ColorType
from osaf.pim import ContentCollection

from i18n import OSAFMessageFactory as _


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
    
    renameable              = schema.One(schema.Boolean, defaultValue = True)
    color                   = schema.One(ColorType)
    iconName                = schema.One(schema.Text)
    iconNameHasKindVariant  = schema.One(schema.Boolean, defaultValue = False)
    colorizeIcon            = schema.One(schema.Boolean, defaultValue = True)
    dontDisplayAsCalendar   = schema.One(schema.Boolean, defaultValue = False)
    outOfTheBoxCollection   = schema.One(schema.Boolean, defaultValue = False)
    canAdd                  = schema.One(schema.Boolean, defaultValue = True)
    allowOverlay            = schema.One(schema.Boolean, defaultValue = True)
    """
      preferredKind is used as a hint to the user-interface to choose the right
      view for the display, e.g. CalendarView for collections that have a preferredKind
      of CalendarEventMixin's kind.
    """
    preferredKind           = schema.One(schema.TypeReference('//Schema/Core/Kind'))

    schema.addClouds(
        copying = schema.Cloud(byRef=[preferredKind]),
    )

    """
      A dictionary mapping a KindName string to a new displayName.
    """
    displayNameAlternatives = schema.Mapping (schema.Text)

    def ensureColor(self):
        """
        setup the color of a collection
        """
        if not hasattr (self, 'color'):
            self.color = schema.ns('osaf.usercollections', self.itsItem.itsView).collectionColors.nextColor()
        return self

    def setValues(self, **kwds):

        for attr,value in kwds.iteritems():
            setattr(self, attr, value)


# Collection colors
# in the form 'Color', _('LocalizableColorString'), 360-degree based hue
import colorsys
collectionHues = [('Blue', _(u'Blue'), 210),
                  ('Green', _(u'Green'), 120),
                  ('Rose', _(u'Rose'), 0),
                  ('Salmon', _(u'Salmon'), 30),
                  ('Purple', _(u'Purple'), 270),
                  ('Violet', _(u'Violet'), 240),
                  ('Fuschia', _(u'Fuschia'), 330)]

def installParcel(parcel, oldVersion=None):

    collectionColors = CollectionColors.update(parcel, 'collectionColors',
        colors = [],
        colorIndex = 0
    )

    for shortName, title, hue in collectionHues:
        rgb = colorsys.hsv_to_rgb(hue/360.0, 0.5, 1.0)
        ct = ColorType(rgb[0]*255, rgb[1]*255, rgb[2]*255, 255)
        collectionColors.colors.append(ct)

    # setup up defaults for well-known parcels
    pim_ns = schema.ns('osaf.pim', parcel.itsView)

    allUC = UserCollection(pim_ns.allCollection)
    allUC.setValues(renameable=False,
                    outOfTheBoxCollection=True,
                    allowOverlay = False, # bug 5818
                    displayNameAlternatives = \
                    {'None': _(u'My items'),
                     'MailMessageMixin': _(u'My mail'),
                     'CalendarEventMixin': _(u'My calendar'),
                     'TaskMixin': _(u'My tasks')})
    allUC.ensureColor()
                                                   
    trashUC = UserCollection(pim_ns.trashCollection)
    trashUC.setValues(renameable=False,
                      dontDisplayAsCalendar=True,
                      outOfTheBoxCollection = True,
                      allowOverlay = False,
                      canAdd=False)
    trashUC.ensureColor()

    inUC = UserCollection(pim_ns.inCollection)
    inUC.setValues(renameable = False,
                   dontDisplayAsCalendar=True)

    outUC = UserCollection(pim_ns.outCollection)
    outUC.setValues(renameable = False,
                    dontDisplayAsCalendar=True)
    

        
