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


"""Dump and Reload module"""

import logging, cPickle, sys, os
from osaf import pim, sharing
from osaf.sharing.eim import uri_registry, RecordClass
from application import schema

logger = logging.getLogger(__name__)

class UnknownRecord(object):
    """Class representing an unknown record type"""
    def __init__(self, *args):
        self.data = args
        
    
class PickleSerializer(object):
    """ Serializes to a byte-length string, followed by newline, followed by
        a pickle string of the specified length """

    @classmethod
    def dumper(cls, output):
        pickler = cPickle.Pickler(output, 2)
        pickler.persistent_id = cls.persistent_id
        return pickler.dump

    @classmethod
    def loader(cls, input):
        unpickler = cPickle.Unpickler(input)
        unpickler.persistent_load = cls.persistent_load
        return unpickler.load

    @staticmethod
    def persistent_id(ob):
        if isinstance(ob, RecordClass):
            # save record classes by URI *and* module
            return ob.URI, ob.__module__   

    @staticmethod
    def persistent_load((uri, module)):
        try:
            return uri_registry[uri]
        except KeyError:
            pass
        # It wasn't in the registry by URI, see if we can import it
        if module not in sys.modules:
            try:
                schema.importString(module)
            except ImportError:
                pass
        try:
            # Maybe it's in the registry now...
            return uri_registry[uri]
        except KeyError:
            # Create a dummy record type for the object
            # XXX this really should try some sort of persistent registry
            #     before falling back to a fake record type
            #
            rtype = type("Unknown", (UnknownRecordType,), dict(URI=uri))
            uri_registry[uri] = rtype
            return rtype


def dump(rv, filename, uuids=None, translator=sharing.DumpTranslator,
    serializer=PickleSerializer, activity=None):
    """
    Dumps EIM records to a file, file permissions 0600.
    """

    if uuids is None:
        uuids = set()
        for item in schema.Item.iterItems(rv):
            if not str(item.itsPath).startswith("//parcels"):
                uuids.add(item.itsUUID)

    trans = translator(rv)

    trans.startExport()

    try:
        flags = os.O_EXCL | os.O_CREAT | os.O_WRONLY | os.O_BINARY
    except AttributeError:
        flags = os.O_EXCL | os.O_CREAT | os.O_WRONLY

    try:
        # Need to remove the file, otherwise we'll use existing permissions
        os.remove(filename)
    except OSError:
        pass
    # XXX This will fail if someone created the file after the remove but
    # XXX before we got here, so the caller should be prepared to handle that.
    output = os.fdopen(os.open(filename, flags, 0600), 'wb')
    try:
        dump = serializer.dumper(output)

        if activity:
            count = len(uuids)
            activity.update(msg="Dumping %d records" % count, totalWork=count)

        i = 0
        for uuid in uuids:
            for record in trans.exportItem(rv.findUUID(uuid)):
                dump(record)
                i += 1
                if activity:
                    activity.update(msg="Dumped %d of %d records" % (i, count),
                        work=1)

        if activity:
            activity.update(totalWork=None) # we don't know upcoming total work

        for record in trans.finishExport():
            if activity:
                count += 1
                activity.update(msg="Dumping additional record")

            dump(record)

        dump(None)
        del dump
    finally:
        output.close()

    if activity:
        activity.update(msg="Dumped %d records" % count)



def reload(rv, filename, translator=sharing.DumpTranslator,
    serializer=PickleSerializer, activity=None):

    """ Loads EIM records from a file and applies them """

    trans = translator(rv)
    trans.startImport()

    input = open(filename, "rb")
    try:
        if activity:
            activity.update(totalWork=None)

        load = serializer.loader(input)
        i = 0
        while True:
            record = load()
            if not record:
                break
            trans.importRecord(record)
            i += 1
            if activity:
                activity.update(msg="Imported %d records" % i)
        del load
    finally:
        input.close()

    trans.finishImport()
