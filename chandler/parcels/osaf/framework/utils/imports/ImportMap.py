"""ImportMap trees map dictionaries into connected repository Items."""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import mx.DateTime as DateTime

class ImportMap:
    """Base class for ImportMap trees.
    
    @ivar parentMap: The parent L{ImportMap} of this branch, or None if
        this is the root of the mapping tree.
    @ivar name: The name of the attribute on the parent this branch applies to,
        or None if this is the root of the mapping tree.
    @ivar kind: If this is the root of the mapping tree, the kind of the tree.
        Otherwise None.
    
    """       
    def process(self, itemDict):
        """Return a filled item, or None if all children map to empty keys.
    
        @param itemDict: Dictionary of values for the current item.
        @type itemDict: A dictionary
        @return: None, or the value of the attribute.
        
        """
        pass

    def getType(self):
        """Return the branch's Type."""
        if self.kind: return self.kind
        else:
            return self.parentMap.getType().getAttribute(self.name).type

class AttributeCollection(ImportMap):
    """A collection of L{ImportMap}s of a particular Kind.

    @ivar maps: A list of L{ImportMap}s.

    """
    def __init__(self, maps=None, kind=None, name=None, parentMap=None):
        if maps:
            self.maps=maps
        else:
            self.maps=[]
        self.name=name
        self.parentMap=parentMap
        self.kind=kind
            
    def process(self, itemDict):
        item=None
        for attrMap in self.maps:
            attr=attrMap.process(itemDict)
            if attr == None: continue
            if not item:
                item=self.getType().newItem(None, None)
            if isinstance(attrMap, ListValue) and \
               isinstance(attrMap.maps[0], AttributeCollection):
                for a in attr:
                    a.move(item)
            elif isinstance(attrMap, AttributeCollection):
                attr.move(item)
            setattr(item, attrMap.name, attr)
        return item

class CondValue(ImportMap):
    """Map for a value to be returned if the mapped key is non-empty."""
    def __init__(self, key, name, value):
        self.key=key
        self.name=name
        self.value=value
        
    def process(self, itemDict):
        if itemDict[self.key]:
            return self.value
        else:
            return None
            
class DateValue(ImportMap):
    """Map for a date value.
    
    @ivar key: The key in itemDict to extract a date from.
    @ivar emptyDates: A list of strings to treat as empty dates.
    @ivar dateType: See formats in mx.DateTime.Parser.DateTimeFromString
    
    """
    def __init__(self, key, name, emptyDates=None, dateType=('us', 'unknown')):
        self.key=key
        self.name=name
        if emptyDates:
            self.emptyDates=[""]+emptyDates
        else:
            self.emptyDates=[""]
        self.dateType=dateType
        
    def process(self, itemDict):
        """Create a RelativeDateTime for itemDict[key]."""        
        dateString=itemDict[self.key]
        if dateString in self.emptyDates:
            return None
        else:
            dateTime= DateTime.Parser.DateTimeFromString(dateString, self.dateType)
            isoString=DateTime.ISO.str(dateTime)
            return DateTime.Parser.RelativeDateTimeFromString(isoString)


class StringValue(ImportMap):
    """Map for a key whose value is a string."""
    def __init__(self, key, name):
        self.key=key
        self.name=name

    def process(self, itemDict):
        if itemDict[self.key]:
            return itemDict[self.key]
        else:
            return None

class ListValue(ImportMap):
    """Map for an attribute whose value should be a list.

    @ivar maps: A list of L{ImportMap}s.

    """
    def __init__(self, maps=None, name=None, parentMap=None):
        if maps:
            self.maps=maps
        else:
            self.maps=[]
        self.name=name
        self.parentMap=parentMap
        self.kind=None
        
    def process(self, itemDict):
        itemlist=[attrMap.process(itemDict) for attrMap in self.maps]
        itemlist=filter(None, itemlist)
        if len(itemlist) > 0: return itemlist
        else: return None

    def getType(self):
        """Give parent's type, because the list itself doesn't have a type."""
        return self.parentMap.getType()

class ConcatKeys(ImportMap):
    """Map for the concatenation of strings.

    @ivar keys: A list of keys to concatenate.

    """
    def __init__(self, keys, name):
        self.keys=keys
        self.name=name

    def process(self, itemDict):
        valueList=[itemDict[key] for key in self.keys]
        lines=os.linesep.join(valueList)
        if lines.strip() == "":
            return None
        else:
            return lines
