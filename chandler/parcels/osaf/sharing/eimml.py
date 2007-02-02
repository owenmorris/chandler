

from application import schema
from osaf.sharing import model, eim
from osaf.sharing.simplegeneric import generic
from osaf.pim.calendar.TimeZone import convertToICUtzinfo
from PyICU import ICUtzinfo
import time, datetime, base64, decimal
from dateutil.parser import parse as dateutilparser
from xml.etree.cElementTree import (
    Element, SubElement, ElementTree, parse, tostring, fromstring
)



__all__ = [
    'EIMMLSerializer',
]








@generic
def serializeValue(typeinfo, value):
    """Serialize a value based on typeinfo"""
    raise NotImplementedError("Unrecognized type:", typeinfo)

@serializeValue.when_type(eim.BytesType)
def serialize_bytes(typeinfo, value):
    return base64.b64encode(value), "bytes"

@serializeValue.when_type(eim.IntType)
def serialize_int(typeinfo, value):
    return str(value), "integer"

@serializeValue.when_type(eim.TextType)
def serialize_text(typeinfo, value):
    return value, "text"

@serializeValue.when_type(eim.BlobType)
def serialize_blob(typeinfo, value):
    return base64.b64encode(value), "blob"

@serializeValue.when_type(eim.ClobType)
def serialize_clob(typeinfo, value):
    return value, "clob"

@serializeValue.when_type(eim.DateType)
def serialize_date(typeinfo, value):
    return value.isoformat(), "datetime"

@serializeValue.when_type(eim.DecimalType)
def serialize_decimal(typeinfo, value):
    return str(value), "decimal"




@generic
def deserializeValue(typeinfo, text):
    """Deserialize text based on typeinfo"""
    raise NotImplementedError("Unrecognized type:", typeinfo)

@deserializeValue.when_type(eim.BytesType)
def deserialize_bytes(typeinfo, text):
    return base64.b64decode(text)

@deserializeValue.when_type(eim.IntType)
def deserialize_int(typeinfo, text):
    return int(text)

@deserializeValue.when_type(eim.TextType)
def deserialize_text(typeinfo, text):
    return text

@deserializeValue.when_type(eim.BlobType)
def deserialize_blob(typeinfo, text):
    return base64.b64decode(text)

@deserializeValue.when_type(eim.ClobType)
def deserialize_clob(typeinfo, text):
    return text

@deserializeValue.when_type(eim.DecimalType)
def deserialize_decimal(typeinfo, text):
    return decimal.Decimal(text)

@deserializeValue.when_type(eim.DateType)
def deserialize_date(typeinfo, text):
    return convertToICUtzinfo(dateutilparser(text))





eimURI = "http://osafoundation.org/eim"
keyURI = "{%s}key" % eimURI
typeURI = "{%s}type" % eimURI
deletedURI = "{%s}deleted" % eimURI

class EIMMLSerializer(object):

    @classmethod
    def serialize(cls, recordSets, rootName="collection", **extra):
        """ Convert a list of record sets to XML text """


        rootElement = Element("{%s}%s" % (eimURI, rootName), **extra)

        for uuid, recordSet in recordSets.iteritems():

            if recordSet is not None:

                recordSetElement = SubElement(rootElement,
                    "{%s}recordset" % eimURI, uuid=uuid)

                for record in list(recordSet.inclusions):
                    recordElement = SubElement(recordSetElement,
                        "{%s}record" % (record.URI))

                    for field in record.__fields__:
                        value = record[field.offset]

                        if value is eim.NoChange:
                            continue

                        else:
                            if value is not None:
                                serialized, typeName = serializeValue(
                                    field.typeinfo, record[field.offset])
                            else:
                                serialized = typeName = None

                            if isinstance(field, eim.key):
                                attrs = { keyURI : 'true' }
                                if typeName is not None:
                                    attrs[typeURI] = typeName
                                fieldElement = SubElement(recordElement,
                                    "{%s}%s" % (record.URI, field.name),
                                    **attrs)
                            else:
                                attrs = { }
                                if typeName is not None:
                                    attrs[typeURI] = typeName
                                fieldElement = SubElement(recordElement,
                                    "{%s}%s" % (record.URI, field.name),
                                    **attrs)

                            fieldElement.text = serialized

                for record in list(recordSet.exclusions):
                    attrs = { deletedURI : "true"}
                    recordElement = SubElement(recordSetElement,
                        "{%s}record" % (record.URI), **attrs)

                    for field in record.__fields__:
                        if isinstance(field, eim.key):
                            value = record[field.offset]
                            serialized, typeName = serializeValue(
                                field.typeinfo, record[field.offset])
                            attrs = { keyURI : 'true' }
                            if typeName is not None:
                                attrs[typeURI] = typeName
                            fieldElement = SubElement(recordElement,
                                "{%s}%s" % (record.URI, field.name),
                                **attrs)
                            fieldElement.text = serialized

            else: # item deletion indicated

                attrs = { deletedURI : "true"}
                recordSetElement = SubElement(rootElement,
                    "{%s}recordset" % eimURI, uuid=uuid, **attrs)


        return tostring(rootElement)

    @classmethod
    def deserialize(cls, text):
        """ Parse XML text into a list of record sets """

        rootElement = fromstring(text) # xml parser

        recordSets = {}
        for recordSetElement in rootElement:
            uuid = recordSetElement.get("uuid")

            deleted = recordSetElement.get(deletedURI)
            if deleted and deleted.lower() == "true":
                recordSet = None

            else:
                inclusions = []
                exclusions = []

                for recordElement in recordSetElement:
                    ns, name = recordElement.tag[1:].split("}")

                    recordClass = eim.lookupSchemaURI(ns)
                    if recordClass is None:
                        continue    # XXX handle error?  logging?

                    values = []
                    for field in recordClass.__fields__:
                        for fieldElement in recordElement:
                            ns, name = fieldElement.tag[1:].split("}")
                            if field.name == name:
                                if fieldElement.text is None:
                                    value = None
                                else:
                                    value = deserializeValue(field.typeinfo,
                                        fieldElement.text)
                                break
                        else:
                            value = eim.NoChange

                        values.append(value)

                    record = recordClass(*values)

                    deleted = recordElement.get(deletedURI)
                    if deleted and deleted.lower() == "true":
                        exclusions.append(record)
                    else:
                        inclusions.append(record)

                recordSet = eim.RecordSet(inclusions, exclusions)

            recordSets[uuid] = recordSet

        return recordSets, dict(rootElement.items())








class EIMMLSerializerLite(object):

    @classmethod
    def serialize(cls, recordSets, rootName="collection", **extra):
        """ Convert a list of record sets to XML text """

        rootElement = Element("{%s}%s" % (eimURI, rootName), **extra)

        for uuid, recordSet in recordSets.iteritems():
            recordSetElement = SubElement(rootElement,
                "{%s}recordset" % eimURI, uuid=uuid)

            for record in list(recordSet.inclusions):
                fields = {}
                for field in record.__fields__:
                    value = record[field.offset]
                    if value is not None:
                        serialized, typeName = serializeValue(field.typeinfo,
                            record[field.offset])
                        fields[field.name] = serialized
                recordURI = record.URI
                recordElement = SubElement(recordSetElement,
                    "{%s}record" % (recordURI), **fields)

        return tostring(rootElement)

    @classmethod
    def deserialize(cls, text):
        """ Parse XML text into a list of record sets """

        recordSets = {}

        rootElement = fromstring(text) # xml parser

        for recordSetElement in rootElement:
            uuid = recordSetElement.get("uuid")
            records = []

            for recordElement in recordSetElement:
                ns, name = recordElement.tag[1:].split("}")

                recordClass = eim.lookupSchemaURI(ns)
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

            recordSet = eim.RecordSet(records)
            recordSets[uuid] = recordSet

        return recordSets, dict(rootElement.items())











def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'EIMML.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

