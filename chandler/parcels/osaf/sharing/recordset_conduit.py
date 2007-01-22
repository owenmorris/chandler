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
import zanshin

logger = logging.getLogger(__name__)


__all__ = [
    'RecordSetConduit',
    'InMemoryRecordSetConduit',
]


class State(schema.Item):
    agreed = schema.Sequence(schema.Tuple)
    pending_inclusions = schema.Sequence(schema.Tuple)
    pending_exclusions = schema.Sequence(schema.Tuple)



class RecordSetConduit(conduits.BaseConduit):

    translator = schema.One(schema.Class)
    serializer = schema.One(schema.Class)
    syncToken = schema.One(schema.Text, defaultValue="")
    filters = schema.Sequence(schema.Text)

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None):

        rv = self.itsView

        translator = self.translator(rv)

        changedItems = set()

        if self.syncToken:  # We've been synced before
            for item in self.share.contents:
                # TBD: determine which items have actually changed,
                # and also which have been deleted
                changedItems.add(uuid)

        else:               # We've not been synced before
            if self.share.contents is not None:
                for item in self.share.contents:
                    changedItems.add(item.itsUUID.str16())


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
        toSend, toApply, pending = self.merge(rsNewBase, inboundDiff)

        # Apply
        for itemUUID, rs in toApply.items():
            translator.importRecords(rs)

        # Send
        text = self.serializer.serialize(toSend)
        self.put(text)




    def clean_diff(self, state, diff):
        diff = (state + diff) - state

        # Remove any unnecessary exclusions (i.e., those that don't have a
        # match in the state.inclusions)
        inc = list(r.getKey() for r in state.inclusions)
        for r in list(diff.exclusions):
            k = r.getKey()
            if k not in inc:
                diff.exclusions.remove(r)

        return diff




    def merge(self, rsNewBase, inboundDiffs={}, send=True, receive=True):
        """Update states, return send/apply/pending dicts

        rsNewBase is a dict from itemUUID -> recordset for items changed
        since last send.  It must always be supplied.

        inboundDiffs is a dict from itemUUID -> the inbound diff recordset.
        It can be omitted if `receive` is false.
        """
        toApply = {}
        toSend  = {}
        pending = {}

        filter = self.getFilter()

        for uuid in set(rsNewBase) | set(inboundDiffs):
            agreed, old_pending = self.getStates(uuid)
            my_state = filter.sync_filter(rsNewBase.get(uuid, agreed))

            filteredInbound = filter.sync_filter(inboundDiffs.get(uuid,
                eim.RecordSet()))
            their_state = agreed + old_pending + filteredInbound

            ncd = (my_state - agreed) | (their_state - agreed)

            dSend = self.clean_diff(their_state, ncd)
            if dSend:
                toSend[uuid] = dSend

            dApply = self.clean_diff(my_state, ncd)
            if dApply:
                toApply[uuid] = dApply

            if send:
                their_state += dSend

            agreed += ncd

            new_pending = their_state - agreed
            if new_pending:
                pending[uuid] = new_pending

            self.saveStates(uuid, agreed, new_pending)

        return toSend, toApply, pending



    def saveStates(self, uuidString, agreed, new_pending):
        State.update(self, uuidString,
            agreed=list(agreed.inclusions),
            pending_inclusions=list(new_pending.inclusions),
            pending_exclusions=list(new_pending.exclusions))



    def getStates(self, uuidString):
        state = self.getItemChild(uuidString)

        if state is None:
            state = (eim.RecordSet(), eim.RecordSet())

        else:
            tupleNew = tuple.__new__

            # pull out the agreed-upon records
            records = []
            for tup in state.agreed:
                records.append(tupleNew(tup[0], tup))
            agreed = eim.RecordSet(records)

            # pull out the pending records
            inclusions = []
            for tup in state.pending_inclusions:
                inclusions.append(tupleNew(tup[0], tup))
            exclusions = []
            for tup in state.pending_exclusions:
                exclusions.append(tupleNew(tup[0], tup))
            pending = eim.RecordSet(inclusions, exclusions)

            state = (agreed, pending)

        return state




    def getFilter(self):
        filter = eim.Filter(None, u'Temporary filter')
        for uri in getattr(self, 'filters', []):
            filter += eim.lookupSchemaURI(uri)
        return filter







shareDict = { }

class InMemoryRecordSetConduit(RecordSetConduit):

    def get(self):
        self.syncToken, text = self.serverGet(self.shareName, self.syncToken)
        return text

    def put(self, text):
        if self.syncToken:
            self.syncToken = self.serverPost(self.shareName, self.syncToken,
                                             text)
        else:
            self.syncToken = self.serverPut(self.shareName, text)

    def exists(self):
        return shareDict.has_key(self.shareName)

    def destroy(self):
        del shareDict[self.shareName]

    def create(self):
        self._getCollection(self.shareName)

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
        return str(token)

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
        return str(token)

    def serverGet(self, path, token):

        if token:
            token = int(token)
        else:
            token = 0

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

        return str(current), text

    def dump(self):
        print shareDict
