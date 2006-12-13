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

import conduits, errors, formats, eim
from i18n import ChandlerMessageFactory as _
import logging
from application import schema

logger = logging.getLogger(__name__)




class Baseline(schema.Item):
    records = schema.Sequence(schema.Tuple)





class RecordSetConduit(conduits.BaseConduit):

    translator = schema.One(schema.Class)
    serializer = schema.One(schema.Class)
    syncToken = schema.One(schema.Text, initialValue=None)

    def sync(self, modOverride=None, updateCallback=None, forceUpdate=None):

        rv = self.itsView

        translator = self.translator()

        # Determine which items have changed:
        changedItems = set()
        for uuid, version, kind, status, values, references, prevKind in \
            rv.mapHistory(self.itemsMarker.itsVersion, rv.itsVersion):
            # @@@MOR: Doublecheck the above version numbers's are correct
            changedItems.add(uuid)

        rsNewBase = { }
        for uuid in changedItems:
            item = rv.findUUID(uuid)
            if item is not None and item.isLive():
                rs = eim.RecordSet(translator.exportItem(item))
            else:
                rs = eim.RecordSet()
            rsNewBase[uuid] = rs


        # Get inbound diffs
        text = self.get()
        inboundDiff = self.serializer.deserialize(text)

        # Merge
        toSend, toApply, lost = self.merge(rsNewBase, inboundDiff)

        # Apply
        for itemUUID, rs in toApply.items():
            translator.processRecords(rs)

        # Send
        text = self.serializer.serialize(toSend)
        self.put(text)


    def merge(self, rsNewBase, inboundDiff):

        # The new sync algorithm

        toSend = {}
        toApply = {}
        lost = {}

        for itemUUID, rs in inboundDiff.items():
            # Until Cosmo supports diffs, we need to compute the diffs
            # ourselves:
            rsOld = self.getRecordSet(itemUUID)
            dInbound = rs - rsOld

            if itemUUID in rsNewBase:
                dLocal = rsNewBase[itemUUID] - rsOld
                lost[itemUUID] = dLocal.conflicts(dInbound)
                rsNewBase[itemUUID] += dInbound
            toApply[itemUUID] = sync_filter(dInbound)  # @@@MOR Hook up
            rsOld += dInbound
            self.saveRecordSet(itemUUID, rsOld)

        for itemUUID, rs in rsNewBase.items():
            rsOld = self.getRecordSet(itemUUID)
            dOutbound = sync_filter(rs - rsOld)  # @@@MOR Hook up

            # If/when Cosmo supports diffs, use the following line:
            # toSend[itemUUID] = dOutbound

            rsOld += dOutbound

            # ...until Cosmo supports diffs, use the following line:
            toSend[itemUUID] = rsOld

            self.saveRecordSet(itemUUID, rsOld)

        return toSend, toApply, lost



    def saveRecordSet(self, uuidString, recordSet):
        Baseline.update(self.share, uuidString,
            records=list(recordSet.inclusions))



    def getRecordSet(self, uuidString):
        baseline = self.share.getItemChild(uuidString)
        if baseline is None:
            recordSet = eim.RecordSet()
        else:
            # recordSet = RecordSet.from_tuples(baseline.records)
            # Until RecordSet gets fleshed out:
            records = []
            tupleNew = tuple.__new__
            for tup in baseline.records:
                records.append(tupleNew(tup[0], tup))
            recordSet = eim.RecordSet(records)
        return recordSet







class CosmoRecordSetConduit(RecordSetConduit, conduits.HTTPMixin):

    def get(self):
        pass

    def put(self):
        pass






shareDict = { }

class InMemoryRecordSetConduit(RecordSetConduit):

    def get(self):
        self.syncToken, text = self.serverGet(self.shareName, self.syncToken)
        return text

    def put(self, text):
        if self.syncToken is None:
            self.syncToken = self.serverPut(self.shareName, text)
        else:
            self.syncToken = self.serverPost(self.shareName, self.syncToken,
                                             text)


    # simulate cosmo:

    def _getCollection(self, path):
        return shareDict.setdefault(path, { "tokens" : [], "recordsets" : {} })

    def _storeUUIDs(self, tokens, uuids):
        tokens.append(uuids)
        return len(tokens)

    def serverPut(self, path, text):
        recordsets = self.serializer.deserialize(text)
        coll = self._getCollection(path)
        uuids = set()
        for uuid, rs in recordsets.items():
            coll["recordsets"][uuid] = rs
            uuids.add(uuid)
        token = self._storeUUIDs(coll["tokens"], uuids)
        return token

    def serverPost(self, path, token, text):
        token = int(token)
        coll = self._getCollection(path)
        current = len(coll["tokens"])

        if token != current:
            raise errors.TokenMismatch("%s != %s" % (token, current))

        recordsets = self.serializer.deserialize(text)
        uuids = set()
        for uuid, rs in recordsets.items():
            coll["recordsets"][uuid] = rs
            uuids.add(uuid)
        token = self._storeUUIDs(coll["tokens"], uuids)
        return token

    def serverGet(self, path, token):

        if token is None:
            token = 0
        else:
            token = int(token)

        coll = self._getCollection(path)

        current = len(coll["tokens"])
        if token > current:
            raise errors.MalformedToken(token)

        uuids = set()
        for uuid_set in coll["tokens"][token:]:
            uuids |= uuid_set

        recordsets = {}
        for uuid in uuids:
            recordsets[uuid] = coll["recordsets"][uuid]

        text = self.serializer.serialize(recordsets)

        return current, text
