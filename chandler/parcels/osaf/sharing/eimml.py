#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
    'EIMMLSerializerLite',
]








@generic
def serializeValue(typeinfo, value):
    """Serialize a value based on typeinfo"""
    raise NotImplementedError("Unrecognized type:", typeinfo)

@serializeValue.when_type(eim.BytesType)
def serialize_bytes(typeinfo, value):
    if value is None:
        return None, "bytes"
    return base64.b64encode(value), "bytes"

@serializeValue.when_type(eim.IntType)
def serialize_int(typeinfo, value):
    if value is None:
        return None, "integer"
    return str(value), "integer"

@serializeValue.when_type(eim.TextType)
def serialize_text(typeinfo, value):
    if value is None:
        return None, "text"
    return value, "text"

@serializeValue.when_type(eim.BlobType)
def serialize_blob(typeinfo, value):
    if value is None:
        return None, "blob"
    return base64.b64encode(value), "blob"

@serializeValue.when_type(eim.ClobType)
def serialize_clob(typeinfo, value):
    if value is None:
        return None, "clob"
    return value, "clob"

@serializeValue.when_type(eim.DateType)
def serialize_date(typeinfo, value):
    if value is None:
        return None, "datetime"
    return value.isoformat(), "datetime"

@serializeValue.when_type(eim.DecimalType)
def serialize_decimal(typeinfo, value):
    if value is None:
        return None, "decimal"
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





eimURI = "http://osafoundation.org/eim/0"
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

                            attrs = { }

                            if value is eim.Missing:
                                serialized, typeName = serializeValue(
                                        field.typeinfo, None)
                                attrs["missing"] = "true"

                            else:
                                serialized, typeName = serializeValue(
                                        field.typeinfo, value)
                                if value == "":
                                    attrs["empty"] = "true"

                            if typeName is not None:
                                attrs[typeURI] = typeName

                            if isinstance(field, eim.key):
                                attrs[keyURI] = "true"

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


        xmlString = tostring(rootElement)
        return "<?xml version='1.0' encoding='UTF-8'?>%s" % xmlString

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
                                empty = fieldElement.get("empty")
                                missing = fieldElement.get("missing")
                                if empty and empty.lower() == "true":
                                    value = ""
                                elif missing and missing.lower() == "true":
                                    value = eim.Missing
                                else:
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
                        if record is eim.NoChange:
                            record = recordClass(*
                                [(eim.Missing if v is eim.NoChange else v)
                                for v in values]
                            )
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

                            if value is eim.Missing:
                                serialized, typeName = serializeValue(
                                    field.typeinfo, None)
                                SubElement(recordElement,
                                    "{%s}%s" % (record.URI, field.name),
                                    missing="true")

                            else:
                                serialized, typeName = serializeValue(
                                    field.typeinfo, value)

                                if serialized is None:
                                    SubElement(recordElement,
                                        "{%s}%s" % (record.URI, field.name))

                                else:
                                    recordElement.set(field.name, serialized)

                for record in list(recordSet.exclusions):
                    attrs = { deletedURI : "true"}

                    for field in record.__fields__:
                        if isinstance(field, eim.key):
                            value = record[field.offset]
                            serialized, typeName = serializeValue(
                                field.typeinfo, record[field.offset])
                            attrs[field.name] = serialized

                    recordElement = SubElement(recordSetElement,
                        "{%s}record" % (record.URI), **attrs)

            else: # item deletion indicated

                attrs = { deletedURI : "true" }
                recordSetElement = SubElement(rootElement,
                    "{%s}recordset" % eimURI, uuid=uuid, **attrs)

        xmlString = tostring(rootElement)
        return "<?xml version='1.0' encoding='UTF-8'?>%s" % xmlString


    @classmethod
    def deserialize(cls, text):
        """ Parse XML text into a list of record sets """

        recordSets = {}

        rootElement = fromstring(text) # xml parser

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
                        value = recordElement.get(field.name)
                        if value is not None:
                            value = deserializeValue(field.typeinfo, value)
                        else:
                            for fieldElement in recordElement:
                                ns, name = fieldElement.tag[1:].split("}")
                                if field.name == name:
                                    missing = fieldElement.get("missing")
                                    if missing and missing.lower() == "true":
                                        value = eim.Missing
                                    else:
                                        value = None
                                    break
                            else:
                                value = eim.NoChange

                        values.append(value)

                    record = recordClass(*values)

                    deleted = recordElement.get(deletedURI)
                    if deleted and deleted.lower() == "true":
                        if record is eim.NoChange:
                            record = recordClass(*
                                [(eim.Missing if v is eim.NoChange else v)
                                for v in values]
                            )
                        exclusions.append(record)
                    else:
                        inclusions.append(record)

                recordSet = eim.RecordSet(inclusions, exclusions)

            recordSets[uuid] = recordSet

        return recordSets, dict(rootElement.items())











def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'EIMML.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

