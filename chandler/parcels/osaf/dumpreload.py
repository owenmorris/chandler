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
    serializer=PickleSerializer):

    """ Dumps EIM records to a file """

    trans = translator(rv)

    output = open(filename, "wb")

    for uuid in uuids:
        for record in trans.exportItem(rv.findUUID(uuid)):
            serializer.outputRecord(output, record)

    output.close()



def reload(rv, filename, translator=sharing.PIMTranslator,
    serializer=PickleSerializer):

    """ Loads EIM records from a file and applies them """

    trans = translator(rv)
    trans.startImport()

    input = open(filename, "rb")

    while True:
        record = serializer.inputRecord(input)
        if not record:
            break
        trans.importRecord(record)

    input.close()

    trans.finishImport()
