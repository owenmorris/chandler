from osaf import sharing
from osaf.sharing import recordtypes
from osaf.sharing.simplegeneric import generic
from PyICU import ICUtzinfo
import datetime, base64
from elementtree.ElementTree import (
    Element, SubElement, ElementTree, parse, tostring, fromstring
)




def _fixTag(tag):
    # Convert this: '{http://osafoundation.org/eimml/item}record'
    # to this: 'http://osafoundation.org/eimml/item/record'
    return tag[1:].replace("}", "/")

def _splitTag(tag):
    # Convert this: '{http://osafoundation.org/eimml/item}record'
    # to this: ['http://osafoundation.org/eimml/item', 'record']
    return tag[1:].split("}")





@generic
def serializeValue(typeinfo, value):
    """Serialize a value based on typeinfo"""
    raise NotImplementedError("Unrecognized type:", typeinfo)

@serializeValue.when_type(sharing.BytesType)
def serialize_bytes(typeinfo, value):
    return value # ???

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
def serialize_date(typeinfo, value):
    return                                      # TODO



def deserialize_bytes(text):
    return text # ???

def deserialize_int(text):
    return int(text)

def deserialize_text(text):
    return text

def deserialize_lob(text):
    return base64.b64decode(text)

def deserialize_decimal(text):
    return                                      # TODO

def deserialize_date(text):
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



deserializers = {
    sharing.BytesType : deserialize_bytes,
    sharing.IntType : deserialize_int,
    sharing.TextType : deserialize_text,
    sharing.DateType : deserialize_date,
    sharing.LobType : deserialize_lob,
    sharing.DecimalType : deserialize_decimal,
}


class RecordSetSerializer(object):

    recordsURI = "http://osafoundation.org/xyzzy/"
    recordSetURI = "http://osafoundation.org/xyzzy/"

    def serialize(self, recordSets):
        """ Convert a list of record sets to XML text """

        recordsElement = Element("{%s}records" % self.recordsURI)

        for uuid, recordSet in recordSets.iteritems():
            recordSetElement = SubElement(recordsElement,
                "{%s}item" % self.recordSetURI, uuid=uuid)

            for record in recordSet:
                fields = {}
                for field in record.__fields__:
                    fields[field.name] = serializeValue(record[field.offset])
                recordURI = record.getURI()
                recordElement = SubElement(recordSetElement,
                    "{%s}record" % (recordURI), **fields)

        return tostring(recordsElement)


    def deserialize(self, text):
        """ Parse XML text into a list of record sets """

        recordSets = {}

        recordsElement = fromstring(text) # xml parser

        for recordSetElement in recordsElement:
            uuid = recordSetElement.get("uuid")
            # recordSet = RecordSet()

            for recordElement in recordSetElement:
                ns, name = _splitTag(recordElement.tag)

                # recordClass = eim.lookupRecordType(ns)

                # Fake lookup method:
                if ns == "http://osafoundation.org/eimml/item":
                    recordClass = recordtypes.ItemRecord
                elif ns == "http://osafoundation.org/eimml/note":
                    recordClass = recordtypes.NoteRecord
                elif ns == "http://osafoundation.org/eimml/task":
                    recordClass = recordtypes.TaskRecord
                elif ns == "http://osafoundation.org/eimml/event":
                    recordClass = recordtypes.EventRecord

                values = []
                for field in recordClass.__fields__:
                    value = recordElement.get(field.name)
                    if value is not None:
                        value = deserializers[type(field.typeinfo)](value)
                    else:
                        value = sharing.NoChange
                    values.append(value)

                print values
                record = recordClass(*values)
                print record

                ##### If we use subelements instead of attributes:
                ### for fieldElement in recordElement:
                ###     ns, fieldName = _splitTag(fieldElement.tag)
                ###     rawValue = fieldElement.text
                ###     field = _getFieldByName(recordClass, fieldName)
                ###     typeinfo = field.typeinfo
                ###     ### cookedValue = convert(rawValue) # hand waving
                ###     attributes[fieldName] = rawValue

            # recordSets[uuid] = recordSet

        # return recordSets

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
        <item:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" title="Welcome to Cosmo" created_on ="2006-11-29 12:25:31 US/Pacific" />
        <note:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" body="base64-encoded-string" icaluid="1e2d48c0-d66b-494c-bb33-c3d75a1ba66b" />
        <event:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" dtstart="20061130T140000" dtend="20061130T150000" rrule="FREQ=WEEKLY" status="CONFIRMED" />
    </eim:recordset>

</eim:records>
"""


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

s = RecordSetSerializer()
s.deserialize(sample2)
