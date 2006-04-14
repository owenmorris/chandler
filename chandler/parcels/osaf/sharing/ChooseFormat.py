"""Analyze streams, determine what kind of resources they contain."""

import vobject, email
import osaf.mail.message
import osaf.sharing.ICalendar
import application.Globals as Globals

EMAIL_FORMAT, ICALENDAR_FORMAT = range(2)

def guessFormat(stream):
    """
    Currently, if vobject can parse it, it's ICALENDAR_FORMAT, if not, and it
    has a From header, it's an email.
    """
    start = stream.tell()
    try:
        # this is potentially expensive, but vobject is much more picky than
        # email's parser, so false positives seem much less likely trying
        # vobject first
        vobj = vobject.readOne(stream)
        if vobj.behavior == vobject.icalendar.VCalendar2_0:
            return ICALENDAR_FORMAT
        # one day we could test if it's a VCARD...
    except:
        pass
    
    stream.seek(start)    
    try:
        msg = email.message_from_file(stream)
        if msg['From'] is not None:
            return EMAIL_FORMAT
    except:
        pass
    
    return None

def importFileAsFormat(format, filename, view, coll=None,
                       selectedCollection=False):
    """
    Import file, return the item that's imported, or None for multiple items.
    """
    if format == ICALENDAR_FORMAT:
        osaf.sharing.ICalendar.importICalendarFile(filename, view, coll,
                                        selectedCollection = selectedCollection)
        return None
    elif format == EMAIL_FORMAT:
        fp = file(filename)
        text = fp.read()
        fp.close()
        return importEmail(text, view, coll, selectedCollection)

def importEmail(text, view, coll=None, selectedCollection=False):
    item = osaf.mail.message.messageTextToKind(view, text)
    if selectedCollection or coll is None:
        coll = Globals.views[0].getSidebarSelectedCollection()
    if item is not None:
        coll.add(item)
    return item

def importFile(filename, view, coll=None, selectedCollection=False):
    """
    Import file, return the item that's imported, or None for multiple items.
    """
    fp = file(filename)
    format = guessFormat(fp)
    fp.close()
    if format is not None:
        return importFileAsFormat(format, filename, view, coll, selectedCollection)
    return None