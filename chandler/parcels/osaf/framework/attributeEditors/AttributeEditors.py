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


"""
Attribute Editors
"""
__parcel__ = "osaf.framework.attributeEditors"

import wx, logging
from cStringIO import StringIO

import osaf.pim as pim
import osaf.pim.calendar.Calendar as Calendar
from osaf.pim.calendar import shortTZ
import osaf.pim.mail as Mail
from repository.schema.TypeHandler import TypeHandler
#from repository.util.Lob import Lob
from chandlerdb.util.c import Nil
from osaf.framework.blocks import DrawingUtilities, Styles
#from operator import itemgetter
from datetime import datetime, timedelta
from PyICU import ICUError, UnicodeString
from osaf.framework.blocks.Block import BaseWidget
#from osaf.pim.items import ContentItem
from application import schema
from application.dialogs import RecurrenceDialog, TimeZoneList
from util.MultiStateButton import MultiStateBitmapCache

from i18n import ChandlerMessageFactory as _
#from osaf import messages

import parsedatetime.parsedatetime as parsedatetime
import parsedatetime.parsedatetime_consts as ptc
import PyICU
from i18n import getLocale

from BaseAttributeEditor import BaseAttributeEditor
#from AETypeOverTextCtrl import AETypeOverTextCtrl, AENonTypeOverTextCtrl
from DragAndDropTextCtrl import DragAndDropTextCtrl
from StringAttributeEditor import StringAttributeEditor
from colorsys import rgb_to_hsv


logger = logging.getLogger(__name__)

#
# The attribute editor registration mechanism:
# For each editor, there's one or more AttributeEditorMapping objects that
# map a string to the editor classname. Each one maps a different type (and
# possibly format & readonlyness). The AttributeEditorMapping's constructor
# makes sure that all the instances are referenced from the 
# AttributeEditorMappingCollection, which we use to find them at runtime.

class AttributeEditorMapping(schema.Item):
    """ 
    A mapping from a 'type name' (the name of this L{Item}) to a specific
    L{BaseAttributeEditor} subclass.

    This item's name is a type name (of an attribute) that'll cause this
    editor to be used to present or edit that attribute's value, optionally
    followed by a '+'-separated list of words that, if present, influence
    the attribute editor picking process - see L{getAEClass} for a full
    explanation of how it's used.

    @ivar className: class path (python dotted style) to this attribute editor.
    @type className: String
    """
    className = schema.One(schema.Text)

    def __setup__(self):
        """ 
        When we construct an L{AttributeEditorMapping}, we need to make sure
        it gets added to the L{AttributeEditorMappingCollection} that tracks
        them.
        """
        aeMappings = schema.ns("osaf.framework.attributeEditors", self.itsView).aeMappings
        aeMappings.editors.append(self, alias=self.itsName)

    @classmethod
    def register(cls, parcel, aeDict, moduleName):
        for typeName, className in aeDict.items():
            if className.find('.') == -1:
                className = moduleName + '.' + className
            cls.update(parcel, typeName, className=className)


class AttributeEditorMappingCollection(schema.Item):
    """ 
    Singleton item that hosts a collection of all L{AttributeEditorMapping}s
    in existance: L{AttributeEditorMapping}'s constructor adds each new instance
    to us to assure this.
    """
    editors = schema.Sequence(
        AttributeEditorMapping, initialValue=[], inverse=schema.One()
    )
    

def installParcel(parcel, oldVersion=None):
    """ 
    Do initial registry of attribute editors.
    
    @param parcel: The parcel we're installing.
    @type parcel: Parcel
    @param oldVersion: @@@ Always None for now.
    @type oldVersion: NoneType
    """

    # Create our one collection of attribute editor mappings; when each gets
    # created, its __init__ will add it to this collection automagically.
    AttributeEditorMappingCollection.update(parcel, "aeMappings")
    
    # This creates individual AttributeEditor objects, which map
    # a type string (their itsName attribute) to a class name.
    # The resulting AttributeEditor objects are found each runtime using
    # a kind query, below.
    #
    # Only add core classes in this parcel to this list (imitate the mechanism
    # if you have your own; the detail view does this.)
    # 
    # If you do modify this list, please keep it in alphabetical 
    # order by type string.
    aeDict = {
        '_default': 'RepositoryAttributeEditor',
        'Boolean': 'CheckboxAttributeEditor',
        'Contact': 'ContactAttributeEditor',
        'ContactName': 'ContactNameAttributeEditor', 
        'ContentItem': 'StringAttributeEditor', 
        'DateTime': 'DateTimeAttributeEditor', 
        'DateTimeTZ': 'DateTimeAttributeEditor', 
        'DateTime+dateOnly': 'DateAttributeEditor', 
        'DateTimeTZ+dateOnly': 'DateAttributeEditor', 
        'DateTime+timeOnly': 'TimeAttributeEditor',
        'DateTimeTZ+timeOnly': 'TimeAttributeEditor',
        'DateTime+timeZoneOnly': 'TimeZoneAttributeEditor',
        'DateTimeTZ+timeZoneOnly': 'TimeZoneAttributeEditor',
        'EmailAddress': 'EmailAddressAttributeEditor',
        'Integer': 'RepositoryAttributeEditor',
        'Item': 'ItemNameAttributeEditor',
        'image/gif': 'LobImageAttributeEditor',
        'image/jpeg': 'LobImageAttributeEditor',
        'image/png': 'LobImageAttributeEditor',
        'image/tiff': 'LobImageAttributeEditor',
        'Location': 'LocationAttributeEditor',
        'Text': 'StringAttributeEditor',
        'Text+static': 'StaticStringAttributeEditor',
        'Timedelta': 'TimeDeltaAttributeEditor',
        'TimeTransparencyEnum': 'ChoiceAttributeEditor',
        'URL': 'StaticStringAttributeEditor',
        'None+rank': 'RankAttributeEditor',
    }
    AttributeEditorMapping.register(parcel, aeDict, __name__)

_TypeToEditorInstances = {}

def getSingleton (typeName, format=None):
    """
    Get (and cache) a single shared Attribute Editor for this type.
    
    These 'singleton' attribute editor instances are used by the Table block
    and are moved about to edit different items' values as the user selects
    them. We lazily create one of each and cache it at runtime.

    @param typeName: The name of the type of the attribute to be edited
    @type typeName: String
    @param format: Optional, customization for this editor
    @type typeName: String
    @return: The attribute editor instance
    @rtype: BaseAttributeEditor
    """
    if format is None and '+' in typeName:
        (typeName, format) = typeName.split('+')
    try:
        instance = _TypeToEditorInstances [(typeName, format)]
    except KeyError:
        aeClass = getAEClass (typeName, format=format)
        logger.debug("getSingleton(%s, %s) --> %s", 
                     typeName, format, aeClass)
        instance = aeClass()
        _TypeToEditorInstances [(typeName, format)] = instance
    return instance

def getInstance(typeName, cardinality, item, attributeName, readOnly, presentationStyle):
    """
    Get a new unshared instance of the Attribute Editor for this type
    (and optionally, format).

    These unshared instances are used in the detail view; we don't cache them.

    @param typeName: The name of the type of the attribute to be edited,
        optionally including "+"-separated parameters; see L{getAEClass} for
        explanation of how the mechanism works.
    @type typeName: String
    @param item: The item whose attribute is to be edited.
    @type item: Item
    @param attributeName: The attributeName of the item to be edited.
    @type attributeName: String
    @param presentationStyle: Behavior customization for this editor, or None.
    @type presentationStyle: PresentationStyle
    @return: The attribute editor instance
    @rtype: BaseAttributeEditor
    """
    try:
        format = presentationStyle.format
    except AttributeError:
        format = None
    if typeName == "Lob" and hasattr(item, attributeName):
        typeName = getattr(item, attributeName).mimetype
    aeClass = getAEClass(typeName, cardinality, readOnly, format)
    #logger.debug("getAEClass(%s [%s, %s, %s]%s) --> %s", 
                 #attributeName, typeName, cardinality, format, 
                 #readOnly and ", readOnly" or "", aeClass)
    instance = aeClass()        
    return instance

def getAEClass(typeName, cardinality='single', readOnly=False, format=None):
    """ 
    Decide which attribute editor class to use for this type.
    
    We'll try several ways to find an appropriate editor, considering
    cardinality, readonlyness, and format, if any are provided, before
    falling back to not considering them. As a last resort, we'll use the
    '_default' one.

    @param typeName: The type name (or MIME type) of the type we'll be editing.
    @type typeName: String
    @param cardinality: The cardinality of the attribute: 'single', 'list', or 'set'.
    @type cardinality: String
    @param readOnly: True if this attribute is readOnly.
    @type readOnly: Boolean
    @param format: Format customization string, if any.
    @return: the attribute editor class to use.
    @rtype: class
    """
    def generateEditorTags():
        # Generate all permutations, most-complex first.
        formatList = format is not None and ('+%s' % format, '',) or ('',)
        readOnlyList = readOnly and ('+readOnly', '',) or ('',)
        cardinalityList = cardinality != 'single' \
                        and ('+%s' % cardinality, '',) or ('',)
        for c in cardinalityList:
            for f in formatList:
                for r in readOnlyList:
                    yield "%s%s%s%s" % (typeName, c, f, r)
        logger.warn("AttributeEditors.getAEClass: using _default for %s/%s",
                    typeName, format)
        yield "_default"

    uiView = wx.GetApp().UIRepositoryView
    aeMappings = schema.ns("osaf.framework.attributeEditors", uiView).aeMappings
    classPath = None
    for key in generateEditorTags():
        key = aeMappings.editors.resolveAlias(key) # either a UUID or None
        if key is not None:
            classPath = aeMappings.editors[key].className
            break
    assert classPath is not None
    
    parts = classPath.split (".")
    assert len(parts) >= 2, " %s isn't a module and class" % classPath
    className = parts.pop ()
    module = __import__ ('.'.join(parts), globals(), locals(), className)
    assert module.__dict__[className], "Class %s doesn't exist" % classPath
    aeClass = module.__dict__[className]
    return aeClass

        
class wxEditText(DragAndDropTextCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxEditText, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterPressed, id=self.GetId())
        minW, minH = arguments[-1] # assumes minimum size passed as last arg
        self.SetSizeHints(minW=minW, minH=minH)

    def OnEnterPressed(self, event):
        self.blockItem.postEventByName ('EnterPressed', {'text':self.GetValue()})
        event.Skip()

class ItemNameAttributeEditor(StringAttributeEditor):
    """
    The editor used for editing collection names in the sidebar.
    """
    def allowEmpty(self):
        return False

class StaticStringAttributeEditor(StringAttributeEditor):
    """
    To be always static, we pretend to be "edit-in-place", but never in
    'edit' mode.
    """
    def CreateControl(self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        return super(StaticStringAttributeEditor, self).\
               CreateControl(False, True, parentWidget, id, parentBlock, font)
    
    def EditInPlace(self):
        return True

    def ReadOnly (self, (item, attribute)):
        return True

    def isStatic(self, (item, attribute)):
        return True

    def SetAttributeValue(self, item, attributeName, valueString):
        # static strings cannot set their attribute value
        pass

    def EndControlEdit(self, item, attributeName, control):
        # value can't change in a static string, so don't try to update
        pass

class LobImageAttributeEditor(BaseAttributeEditor):

    def ReadOnly(self, (item, attribute)):
        return True

    def CreateControl(self, forEditing, readOnly, parentWidget, id,
                      parentBlock, font):
        return wx.PyControl(parentWidget, id, (0, 0), (0, 0),
                            wx.FULL_REPAINT_ON_RESIZE)

    def BeginControlEdit(self, item, attributeName, control):

        try:
            lob = getattr(item, attributeName)
            input = lob.getInputStream()
            stream = StringIO(input.read())
            input.close()
            image = wx.ImageFromStream(stream)
            bitmap = wx.BitmapFromImage(image)
        except:
            logger.exception("Couldn't load image")
            bitmap = wx.NullBitmap
        
        def onPaint(event):
            control = event.GetEventObject()
            size = control.GetClientSize()
            bitmapSize = bitmap.GetSize()
            if bitmapSize.x and bitmapSize.y:
                scale = min(float(size.x) / float(bitmapSize.x),
                            float(size.y) / float(bitmapSize.y),
                            1.0)
            else:
                scale = 1.0
            dc = wx.PaintDC(control)
            gc = wx.GraphicsContext.Create(dc)
            gc.Scale(scale, scale)
            gc.DrawBitmap(bitmap, 0, 0, bitmapSize.x, bitmapSize.y)

        control.Bind(wx.EVT_PAINT, onPaint)


class DateTimeAttributeEditor(StringAttributeEditor):
    def GetAttributeValue(self, item, attributeName):
        # Never used anymore, since we're drawing ourselves below and we're read-only.
        return u''

    def ReadOnly (self, (item, attribute)):
        # @@@MOR Temporarily disable editing of DateTime.  This AE needs some
        # more robust parsing of the date/time info the user enters.
        return True

    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection=False):
        """
        Draw the date & time, somewhat in the style that Apple Mail does:
        Date left justified, time right justified.
        """
        view = item.itsView
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)

        # Erase the bounding box
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect (rect)

        # Figure out what to draw.
        itemDateTime = getattr (item, attributeName, None) # getattr will work with properties
        if itemDateTime is None:
            return # don't draw anything.
        
        # Is this date the start time of an anytime or allday event?
        # (We won't want to show the time if so, bug 7325)
        hideTime = False
        if attributeName == 'displayDate' and item.displayDateSource == 'startTime':
            event = pim.EventStamp(item)
            hideTime = event.allDay or event.anyTime

        itemDate = itemDateTime.date()
        today = datetime.today()
        todayDate = today.date()
        dateString = None
        timeString = None
        tzWidth = 0
        tzFont = None
        preferDate = True
        if itemDate == todayDate:
            # Today? say so, and show the time if we only have room for one value
            # (unless it's allDay/anyTime)
            preferDate = hideTime
            dateString = _(u'Today')
        elif itemDate == (today + timedelta(days=-1)).date(): 
            # Yesterday? say so.
            dateString = _(u'Yesterday')
        elif itemDate == (today + timedelta(days=1)).date(): 
            # To-morrow? say so.
            dateString = _(u'Tomorrow')
        #else:
            # Do day names for days in the last week.
            # (not anymore, see bug 6707)
            #dateString = pim.weekdayName(itemDateTime)

        if dateString is None:
            dateString = pim.mediumDateFormat.format(view, itemDateTime)
        if timeString is None and not hideTime:
            timeString = pim.shortTimeFormat.format(view, itemDateTime)
            tzString = shortTZ(view, itemDateTime)
            if len(tzString) > 0:
                tzFont = Styles.getFont(grid.blockItem.prefixCharacterStyle)
                tzWidth = dc.GetFullTextExtent(tzString, tzFont)[0]
            tzString = shortTZ(view, itemDateTime)
            if len(tzString) > 0:
                tzFont = Styles.getFont(grid.blockItem.prefixCharacterStyle)
                tzWidth = dc.GetFullTextExtent(tzString, tzFont)[0]

        # Draw inside the lines.
        dc.SetBackgroundMode (wx.TRANSPARENT)
        rect.Inflate (-1, -1)
        dc.SetClippingRect (rect)
        
        dateWidth = dc.GetTextExtent(dateString)[0]
        timeWidth = dc.GetTextExtent(timeString)[0] if not hideTime else 0
        spaceWidth = dc.GetTextExtent('  ')[0]

        # If we don't have room for both values, draw one, clipped if necessary.
        if (dateWidth + spaceWidth + timeWidth + tzWidth) > rect.width:
            if preferDate:
                DrawingUtilities.DrawClippedTextWithDots(dc, dateString, rect)
                hideTime = True # suppress timezone display, bug 9942.
            else:
                if tzWidth:
                    rect.width -= tzWidth
                    
                DrawingUtilities.DrawClippedTextWithDots(dc, timeString, rect,
                                                         alignRight=True)
                if tzWidth:
                    rect.width += tzWidth
        else:
            # Enough room to draw both            
            dc.DrawText(dateString, rect.x + 1, rect.y + 1)
            if not hideTime:
                dc.DrawText(timeString, 
                            rect.x + rect.width - (timeWidth + 2 + tzWidth), 
                            rect.y + 1)

        if tzWidth and not hideTime:
            oldFont = dc.GetFont()
            dc.SetFont(tzFont)
            DrawingUtilities.DrawClippedTextWithDots(dc, tzString, rect,
                                                     alignRight=True)
            dc.SetFont(oldFont)
        
        dc.DestroyClippingRegion()
            
class DateAttributeEditor (StringAttributeEditor):
    
    # natural language strings for date
    dateStr = [(u'Today',_(u'Today')), (u'Tomorrow',_(u'Tomorrow')),
                     ( u'Yesterday',_(u'Yesterday')), (u'EOW',_(u'End of week'))]
    
    # Add weekdays of the current locale
    us_weekDays = PyICU.DateFormatSymbols(PyICU.Locale.getUS()).getWeekdays()
    current_weekDays = PyICU.DateFormatSymbols().getWeekdays()
    dateStr.extend(zip(us_weekDays,current_weekDays))
    
    # Add month names of the current locale
    us_months = PyICU.DateFormatSymbols(PyICU.Locale.getUS()).getMonths()
    current_months = PyICU.DateFormatSymbols().getMonths()
    dateStr.extend(zip(us_months,current_months))
    
    textMatches = dict(dateStr)

    
    @classmethod
    def parseDate(cls, view, target):
        """Parses Natural Language date strings using parsedatetime library."""
        target = target.lower()
        for matchKey in cls.textMatches:
            #natural language string for date found
            if ((cls.textMatches[matchKey]).lower()).startswith(target):
                cal = parsedatetime.Calendar()
                (dateVar, invalidFlag) = cal.parse(matchKey)
                #invalidFlag = 0 implies no date/time
                #invalidFlag = 2 implies only time, no date
                if invalidFlag != 0 and invalidFlag != 2:
                    dateStr = pim.shortDateFormat.format(view, datetime(*dateVar[:3]))
                    matchKey = cls.textMatches[matchKey]+ " : %s" % dateStr
                    yield matchKey
            else:
                cal = parsedatetime.Calendar(ptc.Constants(str(getLocale())))
                (dateVar, invalidFlag) = cal.parse(target)
                #invalidFlag = 0 implies no date/time
                #invalidFlag = 2 implies only time, no date
                if invalidFlag != 0 and invalidFlag != 2:
                    # temporary fix: parsedatetime sometimes returns day == 0
                    if not filter(lambda x: not x, dateVar[:3]):
                        match = pim.shortDateFormat.format(view, datetime(*dateVar[:3]))
                        if unicode(match).lower() != target:
                            yield match
                        break
                

    def GetAttributeValue (self, item, attributeName):
        dateTimeValue = getattr(item, attributeName, None)
        value = dateTimeValue and \
                pim.shortDateFormat.format(item.itsView, dateTimeValue) or u''
        return value

    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()

        if len(newValueString) == 0:
            return # leave the value alone if the user clears it out.

        oldValue = getattr(item, attributeName, None)
        if oldValue is None:
            oldValue = datetime.now(item.itsView.tzinfo.default).\
                       replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            dateValue = pim.shortDateFormat.parse(item.itsView, newValueString, 
                                                  referenceDate=oldValue)
        except (ICUError, ValueError):
            self._changeTextQuietly(self.control, "%s ?" % newValueString)
            return
        

        # If this results in a new value, put it back.
        if oldValue is not None:
            value = datetime.combine(dateValue.date(), oldValue.timetz())
        elif dateValue:
            value = dateValue.replace(tzinfo=item.itsView.tzinfo.floating)
        else:
            value = None
        if oldValue != value:
            setattr(item, attributeName, value)
            
        # Refresh the value in place
        if not item.isDeleted():
            self.SetControlValue(self.control, 
                                 self.GetAttributeValue(item, attributeName))
    
    def GetSampleText(self, item, attributeName):
        return pim.sampleDate # get a hint like "mm/dd/yy"
        
    def generateCompletionMatches(self, target):
        view = wx.GetApp().UIRepositoryView
        return self.parseDate(view, target)
        
    def finishCompletion(self, completionString):
        if completionString is not None:
            dashIndex = completionString.find(' : ')
            if dashIndex != -1: # could be 'tomorrow - 08/02/2006'
                completionString = completionString[dashIndex + 3:]
        return super(DateAttributeEditor, self).finishCompletion(completionString)

    
class TimeAttributeEditor(StringAttributeEditor):

    #natural language strings for time
    textMatches = {'Lunch':_(u'Lunch'),'Evening':_(u'Evening'),'Noon':_(u'Noon'),
                   'Midnight':_(u'Midnight'),'Breakfast':_(u'Breakfast'),'Now':_(u'Now'),
                   'Morning':_(u'Morning'),'Dinner':_(u'Dinner'),'Tonight':_(u'Tonight'),
                   'Night':_(u'Night'),u'EOD':_(u'End of day')}
    
    @classmethod
    def parseTime(cls, view, target):
        """Parses Natural Language time strings using parsedatetime library."""
        target = target.lower()
        for matchKey in cls.textMatches:
            #natural language time string found
            if ((cls.textMatches[matchKey]).lower()).startswith(target):
                cal = parsedatetime.Calendar() 
                (timeVar, invalidFlag) = cal.parse(matchKey)
                #invalidFlag = 0 implies no date/time
                #invalidFlag = 1 implies only date, no time
                if invalidFlag != 0 and invalidFlag != 1:
                    timeVar = pim.shortTimeFormat.format(view, datetime(*timeVar[:5]))
                    matchKey = cls.textMatches[matchKey]+ " - %s" %timeVar
                    yield matchKey
            else:
                cal = parsedatetime.Calendar() 
                (timeVar, invalidFlag) = cal.parse(target)
                #invalidFlag = 0 implies no date/time
                #invalidFlag = 1 implies only date, no time
                if invalidFlag != 0 and invalidFlag != 1:
                    match = pim.shortTimeFormat.format(view, datetime(*timeVar[:5]))
                    if unicode(match).lower() !=target:
                        yield match
                    break

    def GetAttributeValue(self, item, attributeName):
        dateTimeValue = getattr(item, attributeName, None)
        value = dateTimeValue and \
                pim.shortTimeFormat.format(item.itsView, dateTimeValue) or u''
        return value

    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()
        if len(newValueString) == 0:
            return # leave the value alone if the user clears it out.
        
        # We have _something_; parse it.
        oldValue = getattr(item, attributeName, None)
        if oldValue is None:
            oldValue = datetime.now(item.itsView.tzinfo.default)
        try:
            timeValue = pim.shortTimeFormat.parse(item.itsView, newValueString, 
                                                  referenceDate=oldValue)
        except ICUError:
            self._changeTextQuietly(self.control, "%s ?" % newValueString)
            return
            
        # If we got a new value, put it back.
        value = datetime.combine(oldValue.date(), timeValue.timetz())
        # Preserve the time zone!
        value = value.replace(tzinfo=oldValue.tzinfo)
        
        if value != oldValue:
            setattr(item, attributeName, value)
            
        # Refresh the value in the control
        self.SetControlValue(self.control, 
                             self.GetAttributeValue(item, attributeName))

    def generateCompletionMatches(self, target):
        """
        A really simple autocompletion example: if the only entry would
        be a valid hour, provide completion of AM & PM versions of it.

        Note: @@@ This may not be right for the product, but I'm leaving it in for now.
        """

        view = wx.GetApp().UIRepositoryView
        try:
            hour = int(target)
        except ValueError:
            for matchKey in self.parseTime(view, target):
                yield matchKey
        else:
            if hour < 24:
                if hour == 12:
                    yield pim.shortTimeFormat.format(view, datetime(2003,10,30,0,00))
                yield pim.shortTimeFormat.format(view, datetime(2003,10,30,hour,00))
                if hour < 12:
                    yield pim.shortTimeFormat.format(view, 
                        datetime(2003,10,30,hour + 12,00))

    def finishCompletion(self, completionString):
        if completionString is not None:
            dashIndex = completionString.find(' - ')
            if dashIndex != -1: # could be 'noon - 12:00 PM'
                completionString = completionString[dashIndex + 3:]
        return super(TimeAttributeEditor, self).finishCompletion(completionString) 
        
    def GetSampleText(self, item, attributeName):
        return pim.sampleTime # Get a hint like "hh:mm PM"

class RepositoryAttributeEditor (StringAttributeEditor):
    """
    Uses Repository Type conversion to provide String representation.
    """
    def ReadOnly (self, (item, attribute)):
        return False # Force editability even if we're in the "read-only" part of the repository

    def GetAttributeValue (self, item, attributeName):
        # attempt to access as a Chandler attribute first
        attrType = item.getAttributeAspect(attributeName, 'type', True)
        value = getattr(item, attributeName, Nil)
        if value is Nil:
            if attrType is None:
                valueString = "no value"
            else:
                valueString = "no value (%s)" % attrType.itsName
        elif attrType is None:
            valueString = str(value)
        else:
            valueString = attrType.makeString(value)

        return valueString

    def SetAttributeValue (self, item, attributeName, valueString):
        # attempt access as a Chandler attribute first
        attrType = item.getAttributeAspect(attributeName, "type", True)
        if attrType is None:
            attrType = TypeHandler.typeHandler(item.itsView, valueString)

        # now we can convert the string to the right type
        value = attrType.makeValue (valueString)
        setattr (item, attributeName, value)

class LocationAttributeEditor (StringAttributeEditor):
    """
    Knows that the data Type is a Location.
    """
    def SetAttributeValue (self, item, attributeName, valueString):
        if not valueString:
            if getattr(item, attributeName, None) is None:
                return # no change
            setattr(item, attributeName, None)
        else:
            # lookup an existing item by name, if we can find it, 
            newValue = Calendar.Location.getLocation (item.itsView, valueString)
            oldValue = getattr(item, attributeName, None)
            if oldValue is newValue:
                return # no change
            setattr (item, attributeName, newValue)
        
    def generateCompletionMatches(self, target):
        view = wx.GetApp().UIRepositoryView
        target = UnicodeString(target).toLower()
        targetLength = len(target)
        for aLoc in Calendar.Location.iterItems(view):
            dispName = UnicodeString(aLoc.displayName).toLower()
            if (dispName[:targetLength] == target
                and dispName != target):
                yield aLoc

class TimeDeltaAttributeEditor (StringAttributeEditor):
    """
    Knows that the data Type is timedelta.
    """

    zeroHours = pim.durationFormat.parse("0:00")
    dummyDate = datetime(2005,1,1)

    def GetAttributeValue (self, item, attributeName):
        # attempt to access as a plain Python attribute
        try:
            value = getattr (item, attributeName)
        except:
            valueString = "HH:MM"
        else:
            valueString = self._format (value)
        return valueString

    def SetAttributeValue (self, item, attributeName, valueString):
        # attempt access as a plain Python attribute
        try:
            value = self._parse(valueString)
        except ValueError:
            pass
        else:
            if self.GetAttributeValue(item, attributeName) != value:
                setattr (item, attributeName, value)

    def _parse(self, inputString):
        """
        Parse the durationString into a timedelta.
        """
        seconds = pim.durationFormat.parse(inputString) - self.zeroHours
        theDuration = timedelta(seconds=seconds)
        return theDuration

    def _format(self, aDuration):
        # if we got a value different from the default
        durationTime = self.dummyDate + aDuration
        value = unicode(pim.durationFormat.format(durationTime))
        return value

class ContactNameAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        contactName = getattr(item, attributeName, Nil)
        if contactName is Nil:
            return ""
        return contactName.firstName + ' ' + contactName.lastName

class ContactAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):

        def computeName(contact):
            return contact.contactName.firstName + ' ' + \
             contact.contactName.lastName

        contacts = getattr(item, attributeName, Nil)
        if contacts is Nil:
            value = ""
        else:
            cardinality = item.getAttributeAspect(attributeName, "cardinality")
            if cardinality == "list":
                value = ', '.join([computeName(contact) for contact in contacts])
            else:
                value = computeName(contacts)
        return value

class EmailAddressAttributeEditor (StringAttributeEditor):
    def __init__(self, *args, **kwargs):
        # make ourselves the delegate for handling strings in the static control
        super(EmailAddressAttributeEditor, self).__init__(staticControlDelegate=self, *args, **kwargs)

    # staticControlDelegate method
    def SetStaticControl(self, control, text):
        if self.showingSample:
            control.SetValue(text)
        else:            
            (addrString, indicatorString, count) = self.shortenAddressList(control, text)

            # Unfortunately, static text controls:
            #   (a) cannot have text appended, and
            #   (b) do not used styled text
            # So no different colour for the indicatorString

            # update the static text control with a representation of 'text'
            control.SetValue(u'%s %s' % (addrString, indicatorString))
 
    def GetAttributeValue(self, item, attributeName):
        attrValue = getattr(item, attributeName, None)
        if attrValue is not None:
            cardinality = item.getAttributeAspect(attributeName, "cardinality")
            if cardinality == 'list':
                # build a string of comma-separated email addresses
                value = u', '.join(map(lambda x: unicode(x), attrValue))
            else:
                # Just format one address
                value = unicode(attrValue)
        else:
            value = u''
        return value

    def shortenAddressList(self, control, addressText):
        """
        Parse a string with a list of email addresses (no validity check, just
        commas) and return both a new string with a list that will fit in the
        given control's bounds, and the number of omitted addresses, in a tuple.
        """
        (ignored, addressList, ignored2) = Mail.EmailAddress.parseEmailAddresses(self.item.itsView, addressText)

        # unrenderedCount is the count of addresses that are not yet considered to
        # be rendered in the text field.  It is used to generate the '[+ N]' string
        # at the end of the field for any addresses that do not fit.
        unrenderedCount = len(addressList)
        addrCount = unrenderedCount

        # maintain two strings: addrOnlyString, which contains
        # a list of addresses separated by ',', and addrString,
        # which has a similar list, with a "[+N]" at the end.
        # addrOnlyString is kept so that the next address can
        # simply be concatenated to the end of it.
        addrString = u''
        addrOnlyString = u''
        indicatorString = u''

        # keep in a variable in case we want to change it later
        unrenderedFormat = u'[+%d]'

        (controlWidth, controlHeight) = control.GetClientSize()

        # Debugging code for trying to figure out why the control shrinks
        # its width by ~32 each time you alternate between two mail messages
        # in the table view
        #
        ##  if controlWidth > 0 and controlWidth < 110:
        ##      import pdb;pdb.set_trace()
        ##  else:
        ##      print "shortenAddressList: ControlWidth is %d" % controlWidth

        # check for zero controlWidth - happens at startup
        if unrenderedCount > 0 and controlWidth > 0:

            # allow for the width of the scrollbar
            controlWidth -= wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X);

            # we always display at least one address
            unrenderedCount -= 1

            def textFitsInControl(addr):
                # the first element of the GetTextExtent call is the width
                # of the rendered text
                return (control.GetTextExtent(addr)[0] < controlWidth)

            def firstAddressFitsInControl(addr):
                """
                Callback that is repeatedly called with potentially shortened
                versions of the first email address, until both the email address
                and any "[+N]" text both fit in the control
                """
                # the first element of the GetTextExtent call is the width
                # of the rendered text
                if unrenderedCount > 0:
                    addr = u"%s [+%d]" % (addr, unrenderedCount)
                return textFitsInControl(addr)

            # get the first address from the list and add the "+N"
            # to the end, if applicable
            #addrOnlyString = unicode(addressList.pop(0))
            addrOnlyString = addressList.pop(0)
            addrOnlyString = addrOnlyString.getShortenedDisplayAddress(firstAddressFitsInControl)
            if unrenderedCount > 0:
                indicatorString = ' [+%d]' % unrenderedCount
                # special case check the first address
                addrString = u'%s %s' % (addrOnlyString, indicatorString)
                # if it's too long to fit even just the first address in the field
                # with an indicator, use a special indicator consisting of just
                # the number of (non visible) addresses
                if not textFitsInControl(addrString):
                    addrString = u''
                    indicatorString = u'[%d addresses]' % unrenderedCount
            # go through the rest of the addresses, building the string and
            # measuring it until the string is too wide to fit in the control
            for addr in addressList:
                # baseAddrString is the nominee to become the new addrOnlyString
                # lengthCheckString is a temporary string to check the length of the
                #     string against the control width
                baseAddrString = u'%s, %s' % (addrOnlyString, unicode(addr))
                unrenderedCount -= 1
                if unrenderedCount > 0:
                    indicatorString = unrenderedFormat % unrenderedCount
                    lengthCheckString = u'%s %s' % (baseAddrString, indicatorString)
                else:
                    indicatorString = u''
                    lengthCheckString = baseAddrString
                if textFitsInControl(lengthCheckString):
                    # it fits, so update the addrOnlyString and try again
                    addrOnlyString = baseAddrString
                else:
                    # it's too big to fit, so use last good addrString
                    # and re-adjust unrenderedCount and indicatorString
                    unrenderedCount += 1
                    indicatorString = unrenderedFormat % unrenderedCount
                    break
        else:
            addrOnlyString = addressText
            unrenderedCount = 0

        return (addrOnlyString, indicatorString, unrenderedCount)

    def SetAttributeValue(self, item, attributeName, valueString):
        # For preview, changes to communication fields should apply to all
        # occurrences, change the master directly
        item = getattr(item, 'proxiedItem', item)
        if pim.has_stamp(item, pim.EventStamp):
            item = pim.EventStamp(item).getMaster().itsItem
        
        processedAddresses, validAddresses, invalidCount = \
            Mail.EmailAddress.parseEmailAddresses(item.itsView, valueString)
        if invalidCount == 0:
            # All the addresses were valid. Put them back.
            cardinality = item.getAttributeAspect (attributeName, "cardinality")
            oldValue = self.GetAttributeValue(item, attributeName)
            if oldValue != processedAddresses:
                if cardinality == 'list':
                    # List cardinality.
                    setattr(item, attributeName, validAddresses)
                else:
                    if len(validAddresses) > 1:
                        # got more than one valid address? That's invalid!
                        processedAddresses = processedAddresses + "?"
                    else:
                        value = len(validAddresses) > 0 \
                              and validAddresses[0] or None
                        setattr(item, attributeName, value)
                    
        if processedAddresses != valueString:
            # This processing changed the text in the control - update it.
            self._changeTextQuietly(self.control, processedAddresses)

    def generateCompletionMatches(self, target):
        view = wx.GetApp().UIRepositoryView
        return Mail.EmailAddress.generateMatchingEmailAddresses(view, target)

class BasePermanentAttributeEditor (BaseAttributeEditor):
    """
    Base class for editors that always need controls.
    """
    def EditInPlace(self):
        return False
    
    def BeginControlEdit (self, item, attributeName, control):
        value = self.GetAttributeValue(item, attributeName)
        self.SetControlValue(control, value)
        control.Enable(not self.ReadOnly((item, attributeName)))

    def EndControlEdit(self, item, attributeName, control):
        # update the item attribute value, from the latest control value.
        # logger.debug("EndControlEdit: '%s' on %s", attributeName, item)
        if not pim.isDead(item):
            value = self.GetControlValue (control)
            self.SetAttributeValue (item, attributeName, value)

class AECheckBox(BaseWidget, wx.CheckBox):
    pass

class CheckboxAttributeEditor (BasePermanentAttributeEditor):
    """
    A checkbox control.
    """
    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection=False):
        # We have to implement Draw, but we don't need to do anything
        # because we've always got a control to do it for us.
        pass

    def CreateControl (self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        
        # Figure out the size we should be
        size = wx.DefaultSize
        if font is not None and parentBlock is not None:
            measurements = Styles.getMeasurements(font)
            try:
                parentWidth = parentBlock.minimumSize.width
            except:
                parentWidth = wx.DefaultSize.width
            size = wx.Size(parentWidth,
                           measurements.checkboxCtrlHeight)

        control = AECheckBox(parentWidget, id, u"", 
                             wx.DefaultPosition, size)
        control.Bind(wx.EVT_CHECKBOX, self.onChecked)
        if readOnly:
            control.Enable(False)
        return control
        
    def onChecked(self, event):
        #logger.debug("CheckboxAE.onChecked: new choice is %s", 
                     #self.GetControlValue(event.GetEventObject()))
        control = event.GetEventObject()
        self.SetAttributeValue(self.item, self.attributeName, \
                               self.GetControlValue(control))

    def GetControlValue (self, control):
        """
        Are we checked?
        """
        return control.IsChecked()

    def SetControlValue (self, control, value):
        """
        Set our state.
        """
        control.SetValue(bool(value))

class AEChoice(BaseWidget, wx.Choice):
    def ActivateInPlace(self):
        """
        Force the pop-up to pop up so the user can select an item.
        """
#       # this is a total hack that doesn't work right now.. 
#       from osaf.framework import scripting
#       scripting.User.emulate_click(self.control, 2, 2)
        pass

    def GetValue(self):
        return self.GetStringSelection()

class ChoiceAttributeEditor(BasePermanentAttributeEditor):
    """
    A pop-up control. The list of choices comes from presentationStyle.choices.
    """
    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection=False):
        """
        Assumes that the attribute is an enum, and uses that to draw
        the locale-sensitive string returned from GetChoices().
        """
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
        # Erase the bounding box
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangleRect (rect)
        
        # get the index of the value, and use that to find the
        # locale-specific value from GetValues()
        value = self.GetAttributeValue(item, attributeName)
        attrType = item.getAttributeAspect(attributeName, 'type')
        choiceIndex = attrType.values.index(value)
        theText = self.GetChoices()[choiceIndex]
        
        rect.Inflate (-1, -1)
        
        dc.SetClippingRect (rect)

        DrawingUtilities.DrawClippedTextWithDots (dc, theText, rect)

        dc.DestroyClippingRegion()

    def CreateControl (self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):

        # Figure out the size we should be
        size = wx.DefaultSize
        if font is not None and parentBlock is not None:
            measurements = Styles.getMeasurements(font)
            try:
                parentWidth = parentBlock.minimumSize.width
            except:
                parentWidth = wx.DefaultSize.width
            size = wx.Size(parentWidth,
                           measurements.choiceCtrlHeight)

        control = AEChoice(parentWidget, id, wx.DefaultPosition, size, [])
        control.Bind(wx.EVT_CHOICE, self.onChoice)
        return control
        
    def onChoice(self, event):
        control = event.GetEventObject()
        newChoice = self.GetControlValue(control)
        # logger.debug("ChoiceAE.onChoice: new choice is %s", newChoice)
        self.SetAttributeValue(self.item, self.attributeName, \
                               newChoice)

    def GetChoices(self):
        """
        Get the choices we're presenting
        """
        return self.presentationStyle.choices

    def GetControlValue (self, control):
        """
        Get the selected choice's text
        """
        choiceIndex = control.GetSelection()
        if choiceIndex == -1:
            return None
        value = self.item.getAttributeAspect(self.attributeName, 'type').values[choiceIndex]
        return value

    def SetControlValue (self, control, value):
        """
        Select the choice with the given text
        """
        # We also take this opportunity to populate the menu
        existingValue = self.GetControlValue(control)
        if existingValue is None or existingValue != value:            
            # rebuild the list of choices
            choices = self.GetChoices()
            control.Clear()
            control.AppendItems(choices)
        
            try:
                choiceIndex = self.item.getAttributeAspect(self.attributeName, 'type').values.index(value)
            except (AttributeError, ValueError):
                # @@@ [grant] The ValueError shouldn't really happen here. But
                # sometimes this code is reached with a value of None, via
                # BeginControlEdit(): I think that what's going on is that
                # when you switch items in the detail view, BeginControlEdit()
                # is called before the various blocks get a chance to
                # hide themselves via shouldShow().
                choiceIndex = 0
            control.Select(choiceIndex)
            
    def BeginControlEdit(self, item, attributeName, control):
        self.item = item
        self.attributeName = attributeName
        self.control = control
        super(ChoiceAttributeEditor, self).BeginControlEdit(item, attributeName, control)

class TimeZoneAttributeEditor(ChoiceAttributeEditor):
    """
    A pop-up control for the tzinfo field of a datetime. The list of
    choices comes from the calendar.TimeZone module.
    """

    def __init__(self, *args, **kwargs):
        super(TimeZoneAttributeEditor, self).__init__(*args, **kwargs)
        self._ignoreChanges = False

    def SetAttributeValue(self, item, attributeName, tzinfo):
        if not self._ignoreChanges:
            oldValue = getattr(item, attributeName, None)

            if oldValue is not None and tzinfo != oldValue.tzinfo:
                # Something changed.                
                value = oldValue.replace(tzinfo=tzinfo)
                setattr(item, attributeName, value)

    def GetAttributeValue(self, item, attributeName):
        value = getattr(item, attributeName, None)
        if value is not None:
            return value.tzinfo
        else:
            return None

    def GetControlValue (self, control):
        """
        Get the selected choice's time zone
        """
        choiceIndex = control.GetSelection()
        if choiceIndex != -1:
            value = control.GetClientData(choiceIndex)
            
            # handle the "Other..." option
            if not self._ignoreChanges and \
               value == TimeZoneList.TIMEZONE_OTHER_FLAG:
                # Opening the pickTimeZone dialog will trigger lose focus, don't
                # process changes to this AE while the dialog is up
                self._ignoreChanges = True
                newTimeZone = TimeZoneList.pickTimeZone(self.item.itsView)
                self._ignoreChanges = False
                # no timezone returned, set the choice back to the item's tzinfo
                if newTimeZone is None:
                    dt = getattr(self.item, self.attributeName, None)
                    if dt is not None:
                        newTimeZone = dt.tzinfo
                TimeZoneList.buildTZChoiceList(self.item.itsView, control,
                                               newTimeZone)
                return newTimeZone
            else:
                return value
        else:
            return None

    def SetControlValue(self, control, value):
        """
        Select the choice with the given time zone
        """

        if value is None:
            value = self.item.itsView.tzinfo.floating

        # We also take this opportunity to populate the menu
        # @@@ for now, we always do it, since we can't tell whether we were
        # called because the prefs changed. This might adversely affect
        # performance, however, which is why I've added this comment.
        #existingValue = self.GetControlValue(control)
        if True: # existingValue is None or existingValue != value:
            # logger.debug("Rebuilding DV timezone popup again") # see how often this happens.
            TimeZoneList.buildTZChoiceList(self.item.itsView, control, value)

class IconAttributeEditor (BaseAttributeEditor):
    """
    Base class for an icon-based attribute editor; subclass and provide
    management of state & variations on the icons.
    """
    bitmapCache = MultiStateBitmapCache()
    noImage = "pixel" # filename of a one-pixel transparent png

    # A mapping from the various variation inputs (is the mouse down? is
    # the mouse over us? are we in a selected row? is this item readonly?)
    # to the variation name we should use
    rolledOverBit = 1
    selectedBit = 2
    mouseDownBit = 4
    readOnlyBit = 8
    variationMap = {
        0 : 'normal',
        rolledOverBit: 'rollover',
        selectedBit: 'selected',
        selectedBit | rolledOverBit: 'rolloverselected',
        mouseDownBit: 'normal', # note, this is the not-rollover case: mouse out
        mouseDownBit | rolledOverBit: 'mousedown', # mouse in
        mouseDownBit | selectedBit: 'selected',
        mouseDownBit | selectedBit | rolledOverBit: 'mousedownselected',
        # @@@ Change these if we need special read/only icons
        readOnlyBit: "normal",
        readOnlyBit | rolledOverBit: "normal",
        readOnlyBit | selectedBit: "selected",
        readOnlyBit | selectedBit | rolledOverBit: 'selected',
        readOnlyBit | mouseDownBit: 'normal', 
        readOnlyBit | mouseDownBit | rolledOverBit: 'normal',
        readOnlyBit | mouseDownBit | selectedBit: 'selected',
        readOnlyBit | mouseDownBit | selectedBit | rolledOverBit: 'selected',
    }

    def __init__(self, *args, **kwds):
        super(IconAttributeEditor, self).__init__(*args, **kwds)
        IconAttributeEditor.bitmapCache.AddStates(\
            multibitmaps=self.makeStates(),
            bitmapProvider=wx.GetApp().GetImage)

    def GetAttributeValue (self, item, attributeName):
        """ 
        Get the current state name. Simple implementation assumes that the 
        configured attribute holds it, and if no attribute value is present,
        no icon should be shown.
        """
        return getattr(item, attributeName, '')
    
    def getImageVariation(self, item, attributeName, isReadOnly, isDown, 
                          isSelected, isOver, justClicked):
        """ Pick the right variation """
        readOnly = isReadOnly and IconAttributeEditor.readOnlyBit or 0
        selected = isSelected and IconAttributeEditor.selectedBit or 0
        mouseDown = isDown and IconAttributeEditor.mouseDownBit or 0
        rolledOver = (not justClicked and isOver) and IconAttributeEditor.rolledOverBit or 0
        return IconAttributeEditor.variationMap[readOnly | selected |
                                                mouseDown | rolledOver]

    def mapValueToIconState(self, state):
        # By default, we use the value as the icon state as-is.
        return state

    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection=False):
        """
        Draw the appropriate variation from the set of icons for this state.
        """
        proxyItem = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
        dc.SetPen (wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect) # always draw the background
        
        isDown = getattr(self, 'wasDown', False)
        isOver = getattr(self, 'rolledOverItem', None) is item
        justClicked = getattr(self, 'justClicked', False)
        isReadOnly = self.ReadOnly((item, attributeName))

        state = self.GetAttributeValue(proxyItem, attributeName)
        if isOver and not justClicked:
            # We want to use the "next" state to determine what to draw.
            nextValueMethod = getattr(self, 'getNextValue', None)
            if nextValueMethod is not None:
                state = nextValueMethod(item, attributeName, state)
        
        iconState = self.mapValueToIconState(state)
        imageSet = self.bitmapCache.get(iconState)
        if imageSet is None:
            return # no images for this state (or we didn't get a state value)

        imageVariation = self.getImageVariation(item, attributeName, isReadOnly,
                                                isDown, isInSelection, isOver,
                                                justClicked)        
        image = getattr(imageSet, imageVariation, None)
        if image is None:
            logger.debug("Hey, missing image!")
        if image is not None:
            x, y, w, h = rect.Get()
            x += (w - image.GetWidth()) / 2
            y += (h - image.GetHeight()) / 2
            dc.DrawBitmap(image, x, y, True)

    def OnMouseChange(self, event):
        """
        Handle live changes of mouse state related to our cell; return True
        if we want the mouse captured for future updates.
        """
        gridWindow = event.GetEventObject()
        item, attributeName = event.getCellValue()

        # do nothing if we're readonly
        if self.ReadOnly((item, attributeName)):
            event.Skip(False)
            return False
        
        # Note whether the item we were over changed
        isIn = event.isInCell
        rolledOverItem = getattr(self, 'rolledOverItem', None)
        inChanged = (not isIn) or (rolledOverItem is not item)
        toolTipMethod = getattr(self, 'getToolTip', None)
        if inChanged:
            if isIn:
                self.rolledOverItem = item
                if toolTipMethod is not None:
                    toolTip = toolTipMethod(item, attributeName)
                    gridWindow.SetToolTipString(toolTip)
            else:
                if hasattr(self, 'rolledOverItem'):
                    del self.rolledOverItem
                if toolTipMethod is not None:
                    gridWindow.SetToolTip(None)

        # Note down-ness changes; eat the event if the downness changed, and
        # trigger an advance if appropriate.
        isDown = event.LeftDown()
        downChanged = isDown != getattr(self, 'wasDown', False)
        advanceStateMethod = getattr(self, 'advanceState', None)
        justClicked = False
        if downChanged and advanceStateMethod is not None:
            if isIn and not isDown:
                advanceStateMethod(item, attributeName)
                if toolTipMethod:
                    toolTip = toolTipMethod(item, attributeName)
                    gridWindow.SetToolTipString(toolTip)
                justClicked = True
            if isDown:
                self.wasDown = True
            else:
                del self.wasDown
            event.Skip(False) # Eat the event
        elif isDown:
            event.Skip(False) # Eat the event to prevent a drag from starting
            
        # Note (or clear) whether we were just clicked
        if justClicked:
            self.justClicked = True
        elif inChanged and hasattr(self, 'justClicked'):
            del self.justClicked
            
        # Redraw ourselves if necessary
        if inChanged or downChanged:
            gridWindow.GetParent().RefreshRect(event.getCellRect())
            
        #logger.debug("IconAttributeEditor (isDown=%s, isIn=%s, %s): %s%s%s",
                     #isDown, isIn, getattr(self, 'rolledOverItem', None),
                     #event.GetSkipped() and "skipping" or "eating",
                     #(inChanged or downChanged) and ", refreshing" or "",
                     #(isIn or isDown) and ", capturing" or "")
        
        # We'll want capture if the mouse is in this cell, or if the mouse is
        # down.
        return isIn or isDown

class RankAttributeEditor (BaseAttributeEditor):
    """
    A special purpose attribute editor that displays order in a collection, currently
    used for display relevancy of search results
    """
    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection = False):
        # Erase the bounding box
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangleRect (rect)
        
        contents = grid.blockItem.contents
        position = contents.positionInIndex ("osaf.views.main.summaryblocks.rank", item)
        rank = float (position) / len (contents)
        if not contents.isDescending ("osaf.views.main.summaryblocks.rank"):
            rank = 1 - rank

        image = wx.GetApp().GetRawImage ("SearchRank.png")
        
        if isInSelection:
            # Set the brightness of the icon to match the brightness
            # of the text color (i.e. text foreground color)
            # so it stands out against the selection background color
            color = dc.GetTextForeground()
            rgbValue = DrawingUtilities.color2rgb(color.Red(), color.Green(), color.Blue())
            hsvValue = rgb_to_hsv(*rgbValue)
            image.SetBrightness (hsvValue[2])

        bitmap = wx.BitmapFromImage (image)

        margin = (bitmap.GetHeight() - rect.GetHeight()) / 2
        if margin > 0:
            margin = 0
        rect.Inflate (-1, margin)
        rect.SetWidth (rect.GetWidth() * rank)
        
        dc.SetClippingRect (rect)
        
        x = rect.GetLeft()
        y = rect.GetTop()
        right = rect.GetRight()
        bitmapWidth = bitmap.GetWidth()

        while x < right:
            dc.DrawBitmap (bitmap, x, y, True)
            x += bitmapWidth

        dc.DestroyClippingRegion()

