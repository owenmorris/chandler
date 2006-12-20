

from application import schema
from osaf import sharing
from osaf.sharing import model
from osaf.sharing.simplegeneric import generic
from PyICU import ICUtzinfo
import time, datetime, base64, decimal
from xml.etree.cElementTree import (
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

@serializeValue.when_type(sharing.BlobType)
def serialize_blob(typeinfo, value):
    return base64.b64encode(value)

@serializeValue.when_type(sharing.ClobType)
def serialize_clob(typeinfo, value):
    return value

@serializeValue.when_type(sharing.DateType)
def serialize_date(typeinfo, value):
    return value.strftime("%Y-%m-%dT%H:%M:%S")

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

@deserializeValue.when_type(sharing.BlobType)
def deserialize_blob(typeinfo, text):
    return base64.b64decode(text)

@deserializeValue.when_type(sharing.ClobType)
def deserialize_clob(typeinfo, text):
    return text

@deserializeValue.when_type(sharing.DecimalType)
def deserialize_decimal(typeinfo, text):
    return decimal.Decimal(text)

@deserializeValue.when_type(sharing.DateType)
def deserialize_date(typeinfo, text):
    tuples = time.strptime(text, "%Y-%m-%dT%H:%M:%S")[0:6]
    utc = ICUtzinfo.getInstance('UTC')
    return datetime.datetime(*tuples).replace(tzinfo=utc)





eimURI = "http://osafoundation.org/eim"

class EIMMLSerializer(object):

    @classmethod
    def serialize(cls, recordSets):
        """ Convert a list of record sets to XML text """

        recordsElement = Element("{%s}records" % eimURI)

        for uuid, recordSet in recordSets.iteritems():
            recordSetElement = SubElement(recordsElement,
                "{%s}recordset" % eimURI, uuid=uuid)

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
            uuid = recordSetElement.get("{%s}uuid" % eimURI)
            records = []

            for recordElement in recordSetElement:
                ns, name = recordElement.tag[1:].split("}")

                recordClass = sharing.lookupSchemaURI(ns)
                if recordClass is None:
                    continue    # XXX handle error?  logging?

                values = []
                for field in recordClass.__fields__:
                    for fieldElement in recordElement:
                        ns, name = fieldElement.tag[1:].split("}")
                        if field.name == name:
                            value = deserializeValue(field.typeinfo,
                                                     fieldElement.text)
                            break
                    else:
                        value = None

                    values.append(value)

                records.append(recordClass(*values))

            recordSet = sharing.RecordSet(records)
            recordSets[uuid] = recordSet

        return recordSets








class EIMMLSerializerLite(object):

    @classmethod
    def serialize(cls, recordSets):
        """ Convert a list of record sets to XML text """

        recordsElement = Element("{%s}records" % eimURI)

        for uuid, recordSet in recordSets.iteritems():
            recordSetElement = SubElement(recordsElement,
                "{%s}item" % eimURI, uuid=uuid)

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
# attributes.  EIMMLSerializerLite handles this format:

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


# This format is what the Cosmo team wants, and is what EIMMLSerializer handles:

sample3 = """<?xml version='1.0' encoding='UTF-8'?>

<eim:records
   xmlns:eim="http://osafoundation.org/eim">
  <eim:recordset
     eim:uuid="f230dcd4-7c32-4c3f-908b-d92081cc9a89">
    <collection:record
       xmlns:collection="http://osafoundation.org/eim/collection"
       eim:uuid="f230dcd4-7c32-4c3f-908b-d92081cc9a89" />
  </eim:recordset>
  <eim:recordset
     eim:uuid="e55b5f1c-a20d-4d47-acda-c43049967281">
    <item:record
       xmlns:item="http://osafoundation.org/eim/item"
       eim:uuid="e55b5f1c-a20d-4d47-acda-c43049967281">
      <item:title eim:type="text"><![CDATA[Welcome to Cosmo!]]></item:title>
      <item:triageStatus eim:type="text" />
      <item:triageStatusChanged eim:type="decimal" />
      <item:lastModifiedBy eim:type="text" />
      <item:createdOn eim:type="datetime"><![CDATA[2006-12-19T11:09:44-0800]]></item:createdOn>
    </item:record>
    <note:record
       xmlns:note="http://osafoundation.org/eim/note"
       eim:uuid="e55b5f1c-a20d-4d47-acda-c43049967281">
      <note:body eim:type="lob"><![CDATA[Welcome to Cosmo!]]></note:body>
      <note:icalUid eim:type="text"><![CDATA[bc54d532-ad87-4c47-b37c-44d23e4f8850]]></note:icalUid>
    </note:record>
    <event:record
       xmlns:event="http://osafoundation.org/eim/event"
       eim:uuid="e55b5f1c-a20d-4d47-acda-c43049967281">
      <event:dtstart eim:type="text"><![CDATA[20061220T090000]]></event:dtstart>
      <event:dtend eim:type="text"><![CDATA[20061220T100000]]></event:dtend>
      <event:location eim:type="text"><![CDATA[]]></event:location>
      <event:rrule eim:type="text" />
      <event:exrule eim:type="text" />
      <event:rdate eim:type="text" />
      <event:exdate eim:type="text" />
      <event:recurrenceId eim:type="text" />
      <event:status eim:type="text" />
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

