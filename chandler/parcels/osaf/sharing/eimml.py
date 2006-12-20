

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

# TODO
# @serializeValue.when_type(sharing.DateType)
# def serialize_date(typeinfo, value):

@serializeValue.when_type(sharing.TimestampType)
def serialize_date(typeinfo, value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")

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

# TODO
# @deserializeValue.when_type(sharing.DateType)
# def deserialize_date(typeinfo, text):

@deserializeValue.when_type(sharing.TimestampType)
def deserialize_date(typeinfo, text):
    tuples = time.strptime(text, "%Y-%m-%dT%H:%M:%SZ")[0:6]
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
                recordElement = SubElement(recordSetElement,
                    "{%s}record" % (record.URI))

                for field in record.__fields__:
                    value = record[field.offset]
                    if value is not None:
                        serialized = serializeValue(field.typeinfo,
                            record[field.offset])
                        if isinstance(field, sharing.key):
                            fieldElement = SubElement(recordElement,
                                "{%s}%s" % (record.URI, field.name), key="true")
                        else:
                            fieldElement = SubElement(recordElement,
                                "{%s}%s" % (record.URI, field.name))
                        fieldElement.text = serialized

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











def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'EIMML.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

