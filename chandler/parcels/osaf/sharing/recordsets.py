

"""
This module supports serializing of EIM recordsets to "EIMML" and back.

>>> from osaf import sharing
>>> class TestRecord(sharing.Record):
...     textField = sharing.field(sharing.TextType(size=100))
...     decimalField = sharing.field(sharing.DecimalType(digits=11,
...                                  decimal_places=2))
...     dateField = sharing.field(sharing.DateType)


Translate text values:

>>> value = deserializeValue(TestRecord.textField.typeinfo, 'xyzzy')
>>> value
'xyzzy'
>>> serializeValue(TestRecord.textField.typeinfo, value)
'xyzzy'


Translate decimal values:

>>> value = deserializeValue(TestRecord.decimalField.typeinfo, '123.45')
>>> value
Decimal("123.45")
>>> serializeValue(TestRecord.decimalField.typeinfo, value)
'123.45'


Translate datetime values:

>>> value = deserializeValue(TestRecord.decimalField.typeinfo, '123.45')
>>> value
Decimal("123.45")
>>> serializeValue(TestRecord.decimalField.typeinfo, value)
'123.45'


TODO: int, lob, bytes


Serialize and deserialize entire record sets:

>>> sample = '''<?xml version="1.0" encoding="UTF-8"?>
...
... <eim:records
... xmlns:eim="http://osafoundation.org/eimml/core"
... xmlns:item="http://osafoundation.org/eimml/item"
... xmlns:event="http://osafoundation.org/eimml/event"
... xmlns:note="http://osafoundation.org/eimml/note">
... <eim:recordset uuid="8501de14-1dc9-40d4-a7d4-f289feff8214">
...    <item:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" title="Welcome to Cosmo" triage_status="now" triage_status_changed="123456789.12" created_on ="2006-11-29 12:25:31 US/Pacific" />
...    <note:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" body="VGhpcyBpcyB0aGUgYm9keQ==" icaluid="1e2d48c0-d66b-494c-bb33-c3d75a1ba66b" />
...    <event:record uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" dtstart="20061130T140000" dtend="20061130T150000" rrule="FREQ=WEEKLY" status="CONFIRMED" />
... </eim:recordset>
... </eim:records>'''

>>> recordSets = deserialize(sample)
>>> recordSets
{'8501de14-1dc9-40d4-a7d4-f289feff8214': RecordSet(set([ItemRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'Welcome to Cosmo', u'now', Decimal("123456789.12"), NoChange, datetime.datetime(2006, 11, 29, 12, 25, 31, tzinfo=<ICUtzinfo: US/Pacific>)), NoteRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'This is the body', u'1e2d48c0-d66b-494c-bb33-c3d75a1ba66b'), EventRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'20061130T140000', u'20061130T150000', NoChange, u'FREQ=WEEKLY', NoChange, NoChange, NoChange, NoChange, u'CONFIRMED')]), set([]))}

>>> text = serialize(recordSets)
>>> text
'<ns0:records xmlns:ns0="http://osafoundation.org/eimml/core"><ns0:item uuid="8501de14-1dc9-40d4-a7d4-f289feff8214"><ns1:record created_on="2006-11-29 12:25:31 US/Pacific" title="Welcome to Cosmo" triage_status="now" triage_status_changed="123456789.12" uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" xmlns:ns1="http://osafoundation.org/eimml/item" /><ns1:record body="VGhpcyBpcyB0aGUgYm9keQ==" icaluid="1e2d48c0-d66b-494c-bb33-c3d75a1ba66b" uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" xmlns:ns1="http://osafoundation.org/eimml/note" /><ns1:record dtend="20061130T150000" dtstart="20061130T140000" rrule="FREQ=WEEKLY" status="CONFIRMED" uuid="8501de14-1dc9-40d4-a7d4-f289feff8214" xmlns:ns1="http://osafoundation.org/eimml/event" /></ns0:item></ns0:records>'

>>> recordSets = deserialize(text)
>>> recordSets
{'8501de14-1dc9-40d4-a7d4-f289feff8214': RecordSet(set([ItemRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'Welcome to Cosmo', u'now', Decimal("123456789.12"), NoChange, datetime.datetime(2006, 11, 29, 12, 25, 31, tzinfo=<ICUtzinfo: US/Pacific>)), NoteRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'This is the body', u'1e2d48c0-d66b-494c-bb33-c3d75a1ba66b'), EventRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'20061130T140000', u'20061130T150000', NoChange, u'FREQ=WEEKLY', NoChange, NoChange, NoChange, NoChange, u'CONFIRMED')]), set([]))}

RecordSets can be stored and retrieved by UUID:

>>> uuidString = '8501de14-1dc9-40d4-a7d4-f289feff8214'
>>> recordSet = recordSets[uuidString]
>>> from repository.persistence.RepositoryView import NullRepositoryView
>>> rv = NullRepositoryView()
>>> share = sharing.Share(itsView=rv)
>>> saveRecordSet(share, uuidString, recordSet)
>>> recordSet = getRecordSet(share, uuidString)
>>> recordSet
RecordSet(set([ItemRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'Welcome to Cosmo', u'now', Decimal("123456789.12"), NoChange, datetime.datetime(2006, 11, 29, 12, 25, 31, tzinfo=<ICUtzinfo: US/Pacific>)), NoteRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'This is the body', u'1e2d48c0-d66b-494c-bb33-c3d75a1ba66b'), EventRecord(u'8501de14-1dc9-40d4-a7d4-f289feff8214', u'20061130T140000', u'20061130T150000', NoChange, u'FREQ=WEEKLY', NoChange, NoChange, NoChange, NoChange, u'CONFIRMED')]), set([]))

(end of doctest)
"""





from osaf import sharing
from osaf.sharing import recordtypes
from osaf.sharing.simplegeneric import generic
from PyICU import ICUtzinfo
import datetime, base64, decimal
from xml.etree.ElementTree import (
    Element, SubElement, ElementTree, parse, tostring, fromstring
)








class Baseline(schema.Item):
    records = schema.Sequence(schema.Tuple)


def saveRecordSet(share, uuidString, recordSet):
    Baseline.update(share, uuidString, records=list(recordSet.inclusions))

def getRecordSet(share, uuidString):
    recordSet = None
    baseline = share.getItemChild(uuidString)
    if baseline is not None:
        # recordSet = RecordSet.from_tuples(baseline.records)
        # Until RecordSet gets fleshed out:
        records = []
        tupleNew = tuple.__new__
        for tup in baseline.records:
            records.append(tupleNew(tup[0], tup))
        recordSet = sharing.RecordSet(records)
    return recordSet





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

def serialize(recordSets):
    """ Convert a list of record sets to XML text """

    recordsElement = Element("{%s}records" % recordsURI)

    for uuid, recordSet in recordSets.iteritems():
        recordSetElement = SubElement(recordsElement,
            "{%s}item" % recordSetURI, uuid=uuid)

        for record in list(recordSet.inclusions):
            fields = {}
            for field in record.__fields__:
                value = record[field.offset]
                if value != sharing.NoChange:
                    serialized = serializeValue(field.typeinfo,
                        record[field.offset])
                    fields[field.name] = serialized
            recordURI = record.URI
            recordElement = SubElement(recordSetElement,
                "{%s}record" % (recordURI), **fields)

    return tostring(recordsElement)


def deserialize(text):
    """ Parse XML text into a list of record sets """

    recordSets = {}

    recordsElement = fromstring(text) # xml parser

    for recordSetElement in recordsElement:
        uuid = recordSetElement.get("uuid")
        records = []

        for recordElement in recordSetElement:
            ns, name = recordElement.tag[1:].split("}")

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
                    value = deserializeValue(field.typeinfo, value)
                else:
                    value = sharing.NoChange
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

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
