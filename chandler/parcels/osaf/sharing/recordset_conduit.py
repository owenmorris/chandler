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

import conduits, errors, formats, serializers, eim
from i18n import ChandlerMessageFactory as _
import logging
from application import schema

logger = logging.getLogger(__name__)




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
        recordSet = eim.RecordSet(records)
    return recordSet





class RecordSetConduit(conduits.BaseConduit):

    # translator = schema.One(eim.Translator)
    translator = schema.One(schema.Item)
    serializer = schema.One(serializers.Serializer)
    syncToken = schema.One(schema.Text)

    def sync(self, modOverride=None, updateCallback=None, forceUpdate=None):

        rv = self.itsView

        # Determine which items have changed:

        changedItems = set()
        for uuid, version, kind, status, values, references, prevKind in \
            rv.mapHistory(self.itemsMarker.itsVersion, rv.itsVersion):
            # @@@MOR: Doublecheck the above version numbers's are correct
            changedItems.add(uuid)

        rsNewBase = { }
        for uuid in changedItems:
            item = rv.findUUID(uuid)
            # @@@MOR: what if item is deleted?
            outbound[uuid] = eim.RecordSet(self.translator.exportItem(item))


        # Get inbound diffs
        inbound = self._get( )

        # Merge
        toSend, toApply, lost = self.merge(self.share, outbound, inbound)

        # Apply
        for itemUUID, rs in toApply.items():
            self.translator.processRecords(rs)

        # Send
        self._put(toSend)


    def merge(self, baselineParent, rsNewBase, inboundDiff=None):

        # The new sync algorithm

        toSend = {}
        toApply = {}
        lost = {}

        for itemUUID, rs in inboundDiff.items():
            # Until Cosmo supports diffs, we need to compute the diffs
            # ourselves:
            rsOld = getRecordSet(baselineParent, itemUUID)
            if rsOld is None:
                rsOld = eim.RecordSet()
            dInbound = rs - rsOld

            if itemUUID in rsNewBase:
                dLocal = rsNewBase[itemUUID] - rsOld
                lost[itemUUID] = dLocal - dInbound
                rsNewBase[itemUUID] += dInbound
            toApply[itemUUID] = sync_filter(dInbound)
            rsOld += dInbound
            saveRecordSet(baselineParent, itemUUID, rsOld)

        for itemUUID, rs in rsNewBase.items():
            rsOld = getRecordSet(baselineParent, itemUUID)
            if rsOld is not None:
                dOutbound = sync_filter(rs - rsOld)
            else:
                dOutbound = sync_filter(rs)
                rsOld = eim.RecordSet()

            # If/when Cosmo supports diffs, use the following line:
            # toSend[itemUUID] = dOutbound

            rsOld += dOutbound

            # ...until Cosmo supports diffs, use the following line:
            toSend[itemUUID] = rsOld

            saveRecordSet(baselineParent, itemUUID, rsOld)

        return toSend, toApply, lost



class CosmoRecordSetConduit(RecordSetConduit, conduits.HTTPMixin):

    def __init__(self, *args, **kw):
        super(CosmoEIMConduit, self).__init__(*args, **kw)

    def _get(self):
        pass

    def _put(self):
        pass

class InMemoryRecordSetConduit(RecordSetConduit, conduits.HTTPMixin):

    def __init__(self, *args, **kw):
        super(InMemoryRecordSetConduit, self).__init__(*args, **kw)

    def _get(self):
        pass

    def _put(self):
        pass

