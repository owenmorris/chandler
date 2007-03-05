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

from osaf.sharing import model, eim

__all__ = [
    'ICSSerializer',
]

# Pseudo-code for Jeffrey

class ICSSerializer(object):

    @classmethod
    def serialize(cls, recordSets, **extra):
        """ Convert a list of record sets to an ICalendar blob """

        vobjects = []
        for uuid, recordSet in recordSets.iteritems():
            vobj = eim_recordset_to_vobject(recordSet)
            vobjects.append(vobj)

        text = serialize_to_ical(vobjects)

        return text


    @classmethod
    def deserialize(cls, text):
        """ Parse an ICalendar blob into a list of record sets """

        recordSets = {}
        extra = {}

        vobjects = parse_ical(text)

        for vobj in vobjects:
            recordSet = vobject_to_eim_recordset(vobj)
            recordSets[uuid_of_item] = recordSet

        return recordSets, extra


