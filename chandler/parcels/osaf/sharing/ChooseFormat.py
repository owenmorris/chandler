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


"""Analyze streams, determine what kind of resources they contain."""

import vobject, email
import osaf.mail.message
import osaf.sharing.ICalendar
from osaf.framework.blocks.Block import Block

EMAIL_FORMAT, EMAILX_FORMAT, ICALENDAR_FORMAT = range(3)

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
        vobj = vobject.readOne(stream, ignoreUnreadable=True)
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

    stream.seek(start)    
    try:
        stream.readline()
        msg = email.message_from_file(stream)
        if msg['From'] is not None:
            return EMAILX_FORMAT
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
        view.commit()
        return None
    elif format in (EMAIL_FORMAT, EMAILX_FORMAT):
        fp = file(filename)
        size = -1
        if format == EMAILX_FORMAT:
            # Apple's .emlx takes an rfc822 message, prepends a line with the
            # length of the normal message, and appends metadata in XML we don't
            # care about
            size = int(fp.readline())
        text = fp.read(size)
        fp.close()
        return importEmail(text, view, coll, selectedCollection)

def importEmail(text, view, coll=None, selectedCollection=False):
    status, msg = osaf.mail.message.messageTextToKind(view, text)
    if selectedCollection or coll is None:
        coll = Block.findBlockByName("MainView").getSidebarSelectedCollection()
    if msg is not None:
        coll.add(msg.itsItem)
    return msg.itsItem

def importFileGuessFormat(filename, view, coll=None, selectedCollection=False):
    """
    Import file, return the item that's imported, or None for multiple items.
    """
    fp = file(filename)
    format = guessFormat(fp)
    fp.close()
    if format is not None:
        return importFileAsFormat(format, filename, view, coll, selectedCollection)
    return None
