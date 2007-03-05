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

import logging, cPickle
from osaf import pim, sharing

logger = logging.getLogger(__name__)


class PickleSerializer(object):
    """ Serializes to a byte-length string, followed by newline, followed by
        a pickle string of the specified length """

    @classmethod
    def outputRecord(cls, output, record):
        text = cPickle.dumps(record)
        output.write("%d\n" % len(text))
        output.write(text)

    @classmethod
    def inputRecord(cls, input):
        line = input.readline()
        if not line:
            return None
        return cPickle.loads(input.read(int(line.strip())))





def dump(rv, filename, uuids, translator=sharing.PIMTranslator,
    serializer=PickleSerializer, activity=None):

    """ Dumps EIM records to a file """

    trans = translator(rv)

    output = open(filename, "wb")

    if activity:
        count = len(uuids)
        activity.update(msg="Dumping %d records" % count, totalWork=count)

    i = 0
    for uuid in uuids:
        for record in trans.exportItem(rv.findUUID(uuid)):
            serializer.outputRecord(output, record)
            i += 1
            if activity:
                activity.update(msg="Dumped %d of %d records" % (i, count),
                    work=1)

    output.close()
    if activity:
        activity.update(msg="Dumped %d records" % count)



def reload(rv, filename, translator=sharing.PIMTranslator,
    serializer=PickleSerializer, activity=None):

    """ Loads EIM records from a file and applies them """

    trans = translator(rv)
    trans.startImport()

    input = open(filename, "rb")
    if activity:
        activity.update(totalWork=None)

    i = 0
    while True:
        record = serializer.inputRecord(input)
        if not record:
            break
        trans.importRecord(record)
        i += 1
        if activity:
            activity.update(msg="Imported %d records" % i)

    input.close()

    trans.finishImport()
