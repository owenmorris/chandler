

from application import schema
from osaf import sharing
from osaf.sharing import model
from osaf.sharing.simplegeneric import generic
from PyICU import ICUtzinfo
import datetime, base64, decimal
from xml.etree.ElementTree import (
    Element, SubElement, ElementTree, parse, tostring, fromstring
)











@generic
def serializeValue(typeinfo, value):
    """Serialize a value based on typeinfo"""
    raise NotImplementedError("Unrecognized type:", typeinfo)

@serializeValue.when_type(sharing.BytesType)
def serialize_bytes(typeinfo, value):
    return value

@serializeValue.when_type(sharing.IntType)
def serialize_int(typeinfo, value):
    return str(value)

@serializeValue.when_type(sharing.TextType)
def serialize_text(typeinfo, value):
    return value

@serializeValue.when_type(sharing.LobType)
def serialize_lob(typeinfo, value):
    return base64.b64encode(value)

@serializeValue.when_type(sharing.DateType)
def serialize_date(typeinfo, value):
    return value.strftime("%Y-%m-%d %H:%M:%S %Z")

@serializeValue.when_type(sharing.DecimalType)
def serialize_decimal(typeinfo, value):
    return str(value)




@generic
def deserializeValue(typeinfo, text):
    """Deserialize text based on typeinfo"""
    raise NotImplementedError("Unrecognized type:", typeinfo)

@deserializeValue.when_type(sharing.BytesType)
def deserialize_bytes(typeinfo, text):
    return text

@deserializeValue.when_type(sharing.IntType)
def deserialize_int(typeinfo, text):
    return int(text)

@deserializeValue.when_type(sharing.TextType)
def deserialize_text(typeinfo, text):
    return text

@deserializeValue.when_type(sharing.LobType)
def deserialize_lob(typeinfo, text):
    return base64.b64decode(text)

@deserializeValue.when_type(sharing.DecimalType)
def deserialize_decimal(typeinfo, text):
    return decimal.Decimal(text)

@deserializeValue.when_type(sharing.DateType)
def deserialize_date(typeinfo, text):
    values = text.split(' ')
    count = len(values)

    if count < 2:
        raise ValueError, text  # Define an error to raise

    if count >= 2:
        try:
            (yyyy, MM, dd) = values[0].split('-')
            (HH, mm, second) = values[1].split(':')
            tz = None
        except ValueError, e:  # Define an error to raise
            e.args = (e.args[0], text)
            raise

    if count >= 3:
        tz = ICUtzinfo.getInstance(values[2])

    second_values = second.split('.')
    second_count = len(second_values)

    if second_count < 1:
        raise ValueError, second # Define an error to raise

    ss = int(second_values[0])

    if second_count > 1:
        v1 = values[1]
        us = int(v1)
        for i in xrange(len(v1), 6):
            us *= 10
    else:
        us = 0

    return datetime.datetime(int(yyyy), int(MM), int(dd),
        int(HH), int(mm), ss, us, tz)





recordsURI = "http://osafoundation.org/eimml/core"
recordSetURI = "http://osafoundation.org/eimml/core"

class EIMMLSerializer(object):

    @classmethod
    def serialize(cls, recordSets):
        """ Convert a list of record sets to XML text """

        recordsElement = Element("{%s}records" % recordsURI)

        for uuid, recordSet in recordSets.iteritems():
            recordSetElement = SubElement(recordsElement,
                "{%s}item" % recordSetURI, uuid=uuid)

            for record in list(recordSet.inclusions):
                fields = {}
                for field in record.__fields__:
                    value = record[field.offset]
                    if value is not None:
                        serialized = serializeValue(field.typeinfo,
                            record[field.offset])
                        fields[field.name] = serialized
                recordURI = record.URI
                recordElement = SubElement(recordSetElement,
                    "{%s}record" % (recordURI), **fields)

        return tostring(recordsElement)

    @classmethod
    def deserialize(cls, text):
        """ Parse XML text into a list of record sets """

        recordSets = {}

        recordsElement = fromstring(text) # xml parser

        for recordSetElement in recordsElement:
            uuid = recordSetElement.get("uuid")
            records = []

            for recordElement in recordSetElement:
                ns, name = recordElement.tag[1:].split("}")

                recordClass = sharing.lookupSchemaURI(ns)
                if recordClass is None:
                    continue    # XXX handle error?  logging?

                values = []
                for field in recordClass.__fields__:
                    value = recordElement.get(field.name)
                    if value is not None:
                        value = deserializeValue(field.typeinfo, value)
                    else:
                        value = None
                    values.append(value)

                records.append(recordClass(*values))

            recordSet = sharing.RecordSet(records)
            recordSets[uuid] = recordSet

        return recordSets










# This is a much more compact xml format, where fields map directly to
# attributes.  The current code handles this format:

sample = """<?xml version="1.0" encoding="UTF-8"?>

<eim:records
    xmlns:eim="http://osafoundation.org/eimml/core"
    xmlns:collection="http://osafoundation.org/eimml/collection"
    xmlns:item="http://osafoundation.org/eimml/item"
    xmlns:event="http://osafoundation.org/eimml/event"
    xmlns:task="http://osafoundation.org/eimml/task"
    xmlns:message="http://osafoundation.org/eimml/message"
    xmlns:note="http://osafoundation.org/eimml/note">

    <eim:recordset uuid="8501de14-1dc9-40d4-a7d4-f289feff8214">
        <item:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" title="Welcome to Cosmo" triage_status="now" triage_status_changed="123456789.12" created_on ="2006-11-29 12:25:31 US/Pacific" />
        <note:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" body="VGhpcyBpcyB0aGUgYm9keQ==" icaluid="1e2d48c0-d66b-494c-bb33-c3d75a1ba66b" />
        <event:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" dtstart="20061130T140000" dtend="20061130T150000" rrule="FREQ=WEEKLY" status="CONFIRMED" />
    </eim:recordset>

</eim:records>
"""


# This is an xml-element-per-field approach, which is a bit verbose.  The
# current code does not handle this format:

sample2 = """<?xml version="1.0" encoding="UTF-8"?>

<eim:records
    xmlns:eim="http://osafoundation.org/eimml/core"
    xmlns:collection="http://osafoundation.org/eimml/collection"
    xmlns:item="http://osafoundation.org/eimml/item"
    xmlns:event="http://osafoundation.org/eimml/event"
    xmlns:task="http://osafoundation.org/eimml/task"
    xmlns:message="http://osafoundation.org/eimml/message"
    xmlns:note="http://osafoundation.org/eimml/note">

    <eim:recordset uuid="8501de14-1dc9-40d4-a7d4-f289feff8214">
        <item:record>
            <item:uuid>8501de14-1dc9-40d4-a7d4-f289feff8214</item:uuid>
            <item:title>Welcome to Cosmo</item:title>
            <item:created_on>2006-11-29T12:25:31-0800</item:created_on>
        </item:record>
        <note:record>
            <note:uuid>8501de14-1dc9-40d4-a7d4-f289feff8214</note:uuid>
            <note:body>This is the body</note:body>
            <note:icaluid>1e2d48c0-d66b-494c-bb33-c3d75a1ba66b</note:icaluid>
        </note:record>
        <event:record>
            <event:uuid>8501de14-1dc9-40d4-a7d4-f289feff8214</event:uuid>
            <event:dtstart>20061130T140000</event:dtstart>
            <event:dtend>20061130T150000</event:dtend>
            <event:rrule>FREQ=WEEKLY</event:rrule>
            <event:status>CONFIRMED</event:status>
        </event:record>
    </eim:recordset>

    <eim:recordset uuid="9501de14-1dc9-40d4-a7d4-f289feff8214">
        <item:record>
            <item:uuid>9501de14-1dc9-40d4-a7d4-f289feff8214</item:uuid>
            <item:title>Welcome to Chandler</item:title>
            <item:created_on>2006-11-29T12:25:31-0800</item:created_on>
        </item:record>
        <note:record>
            <note:uuid>9501de14-1dc9-40d4-a7d4-f289feff8214</note:uuid>
            <note:body>This is the body</note:body>
            <note:icaluid>1e2d48c0-d66b-494c-bb33-c3d75a1ba66b</note:icaluid>
        </note:record>
        <event:record>
            <event:uuid>9501de14-1dc9-40d4-a7d4-f289feff8214</event:uuid>
            <event:dtstart>20061130T140000</event:dtstart>
            <event:dtend>20061130T150000</event:dtend>
            <event:rrule>FREQ=WEEKLY</event:rrule>
            <event:status>CONFIRMED</event:status>
        </event:record>
    </eim:recordset>

</eim:records>
"""

def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'EIMML.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
