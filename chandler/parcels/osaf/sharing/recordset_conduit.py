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

from osaf import pim
import conduits, errors, formats, eim
from i18n import ChandlerMessageFactory as _
import logging
from application import schema
import zanshin
from repository.item.Item import Item

logger = logging.getLogger(__name__)


__all__ = [
    'RecordSetConduit',
    'InMemoryRecordSetConduit',
]

USE_PICKLE = True
if USE_PICKLE:
    import cPickle

class State(schema.Item):
    deleted = schema.One(schema.Boolean, defaultValue=False)

    if USE_PICKLE:
        agreed = schema.One(schema.Text)
        pending = schema.One(schema.Text)
    else:
        agreed = schema.Sequence(schema.Tuple)
        pending_inclusions = schema.Sequence(schema.Tuple)
        pending_exclusions = schema.Sequence(schema.Tuple)


    # TODO: add a biref to the item here (pending_for_item), where the other end is a ref collection, an annotation called pending_states



class RecordSetConduit(conduits.BaseConduit):

    translator = schema.One(schema.Class)
    serializer = schema.One(schema.Class)
    syncToken = schema.One(schema.Text, defaultValue="")
    filters = schema.Sequence(schema.Text)
    baseline = schema.One(schema.ItemRef)


    def __init__(self, *args, **kw):
        super(RecordSetConduit, self).__init__(*args, **kw)
        self.baseline = schema.Item('baseline', self, None)

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):

        if debug: print " ================ start of sync ================= "

        rv = self.itsView

        translator = self.translator(rv)

        if self.share.contents is None:
            self.share.contents = pim.SmartCollection(itsView=rv)

        if self.syncToken:
            version = self.itemsMarker.itsVersion
        else:
            version = -1

        # Get inbound changes
        text = self.get()
        if debug: print "Inbound text:", text

        inboundDiff = self.serializer.deserialize(text)
        if debug: print "Inbound records", inboundDiff

        # Generate records for all local items to be merged -- those that
        # have either been changed locally or remotely:

        remotelyRemoved = set()
        localItems = set()

        # Add remotely changed items
        for uuid in inboundDiff.keys():
            rs = inboundDiff[uuid]
            if rs is None: # skip deletions
                if debug: print "Inbound removal:", uuid
                del inboundDiff[uuid]
                remotelyRemoved.add(uuid)

                # Clear out the agreed state and any pending changes, so
                # that if there are local changes, they'll just get sent
                # back out along with the *complete* state of the item. The
                # item has already been removed from the server, and we're
                # putting it back.
                self.removeState(uuid)

            else:
                if debug: print "Inbound modification:", uuid
                item = rv.findUUID(uuid)
                if item is not None and item.isLive():
                    # An inbound modification to an item we already have
                    localItems.add(uuid)

                elif self.hasState(uuid):
                    # This is an item we completely deleted since our last
                    # sync.  We need to grab its previous state out of the
                    # baseline, apply any pending changes and the new
                    # inbound chagnes to it, and use that as the new
                    # inboundDiff
                    agreed, pending = self.getState(uuid)
                    rs = agreed + pending + rs
                    if debug: print "Reconstituting item from baseline:", rs
                    inboundDiff[uuid] = rs
                    self.removeState(uuid)


        if debug: print "Conduit marker version:", version

        # Add locally changed items
        for item in self.share.contents:
            if debug: print "Examining local item", item, item.itsVersion
            if item.itsVersion > version:
                uuid = item.itsUUID.str16()
                localItems.add(uuid)
                if uuid in remotelyRemoved:
                    # This remotely removed item was modified locally.
                    # We are going to send the whole item back out.
                    remotelyRemoved.remove(uuid)


        # Compute local records
        rsNewBase = { }
        for uuid in localItems:
            item = rv.findUUID(uuid)
            if item is not None and item.isLive():
                rs = eim.RecordSet(translator.exportItem(item))
            else:
                rs = eim.RecordSet()
            rsNewBase[uuid] = rs


        # Merge
        toSend, toApply, pending = self.merge(rsNewBase, inboundDiff,
            debug=debug)


        # Apply
        for uuid, rs in toApply.items():
            if debug: print "Applying:", uuid, rs
            translator.importRecords(rs)


        # Make sure any items that came in are added to the collection
        for uuid in inboundDiff:
            # Add the item to contents
            item = rv.findUUID(uuid)
            if item is not None and item.isLive():
                if debug: print "Adding to collection:", uuid
                self.share.contents.add(item)


        # For each item that was in the collection before but is no longer,
        # add an empty recordset to toSend
        for uuid in self.getBaselineUuids():
            item = rv.findUUID(uuid)
            if (item is None or
                item not in self.share.contents and
                uuid not in remotelyRemoved):
                toSend[uuid] = None
                self.removeState(uuid)
                if debug: print "Remotely removing item:", uuid


        # For each remote removal, remove the item from the collection locally
        # At this point, we know there were no local modifications
        for uuid in remotelyRemoved:
            item = rv.findUUID(uuid)
            if item is not None and item in self.share.contents:
                self.share.contents.remove(item)
                self.removeState(uuid)
                if debug: print "Locally removing item:", uuid


        # Send
        if toSend:
            text = self.serializer.serialize(toSend)
            self.put(text)
            if debug: print "Sent text:", text
        else:
            if debug: print "Nothing to send"


        # Note the repository version number, which will increase at the next
        # commit
        self.itemsMarker.setDirty(Item.NDIRTY)

        if debug: print " ================== end of sync ================= "

    def clean_diff(self, state, diff):
        new_state = state + diff
        new_state.exclusions = set()
        diff = new_state - state
        return diff



    def merge(self, rsNewBase, inboundDiffs={}, send=True, receive=True,
        debug=False):
        """Update states, return send/apply/pending dicts

        rsNewBase is a dict from itemUUID -> recordset for items changed
        since last send, *and* for any items appearing in inboundDiffs (even
        if the item has not been locally changed).  It must always be supplied.

        inboundDiffs is a dict from itemUUID -> the inbound diff recordset.
        It can be omitted if `receive` is false.
        """
        toApply = {}
        toSend  = {}
        pending = {}

        filter = self.getFilter()

        for uuid in set(rsNewBase) | set(inboundDiffs):
            agreed, old_pending = self.getState(uuid)
            if debug:
                print " ----------- Merging item:", uuid
                print "   rsNewBase:", rsNewBase.get(uuid, "Nothing")
                print "   inboundDiff:", inboundDiffs.get(uuid, "Nothing")
                print "   agreed:", agreed
                print "   old_pending:", old_pending

            my_state = filter.sync_filter(rsNewBase.get(uuid, agreed))

            filteredInbound = filter.sync_filter(inboundDiffs.get(uuid,
                eim.RecordSet()))
            their_state = agreed + old_pending + filteredInbound

            ncd = (my_state - agreed) | (their_state - agreed)

            if debug:
                print "   my_state:", my_state
                print "   their_state:", their_state
                print "   ncd:", ncd

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

            self.saveState(uuid, agreed, new_pending)

            if debug:
                print " - - - - Results - - - - "
                print "   agreed:", agreed
                print "   new_pending:", new_pending
                print "   toSend:", toSend
                print "   toApply:", toApply
                print "   pending:", pending
                print " ----------- End of merge "

        return toSend, toApply, pending



    def saveState(self, uuidString, agreed, new_pending):
        if USE_PICKLE:
            State.update(self.baseline, uuidString,
                deleted=False,
                agreed=cPickle.dumps(agreed),
                pending=cPickle.dumps(new_pending))
        else:
            State.update(self.baseline, uuidString,
                deleted=False,
                agreed=list(agreed.inclusions),
                pending_inclusions=list(new_pending.inclusions),
                pending_exclusions=list(new_pending.exclusions))




    def getState(self, uuidString):
        state = self.baseline.getItemChild(uuidString)

        if state is None or state.deleted:
            state = (eim.RecordSet(), eim.RecordSet())

        else:
            if USE_PICKLE:
                agreed = cPickle.loads(state.agreed)
                pending = cPickle.loads(state.pending)
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

    def removeState(self, uuidString):
        state = self.baseline.getItemChild(uuidString)
        if state is not None:
            state.deleted = True

    def hasState(self, uuidString):
        state = self.baseline.getItemChild(uuidString)
        return state is not None and not state.deleted

    def discardPending(self, uuidString):
        if self.hasState(uuidString):
            agreed, pending = self.getState(uuidString)
            self.saveState(uuidString, agreed, eim.RecordSet())

    def getBaselineUuids(self):
        for state in self.baseline.iterChildren():
            if state.isLive():
                yield state.itsName




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
        return shareDict.setdefault(path, { "token" : 0, "items" : {} })


    def serverPut(self, path, text):
        recordsets = self.serializer.deserialize(text)
        coll = self._getCollection(path)
        newToken = coll["token"]
        newToken += 1
        for uuid, rs in recordsets.items():
            itemHistory = coll["items"].setdefault(uuid, [])
            itemHistory.append( (newToken, rs) )
        coll["token"] = newToken
        return str(newToken)

    def serverPost(self, path, token, text):
        token = int(token)
        coll = self._getCollection(path)
        current = coll["token"]

        if token != current:
            raise errors.TokenMismatch("%s != %s" % (token, current))

        return self.serverPut(path, text)

    def serverGet(self, path, token):

        if token:
            token = int(token)
        else:
            token = 0

        coll = self._getCollection(path)

        current = coll["token"]
        if token > current:
            raise errors.MalformedToken(token)


        empty = eim.RecordSet()
        recordsets = { }
        for uuid, itemHistory in coll["items"].iteritems():
            rs = eim.RecordSet()
            for historicToken, diff in itemHistory:
                if historicToken > token:
                    if diff is None:
                        # This item was removed
                        rs = None
                    if diff is not None:
                        if rs is None:
                            rs = eim.RecordSet()
                        rs = rs + diff
            if rs != empty:
                recordsets[uuid] = rs


        text = self.serializer.serialize(recordsets)

        return str(current), text

    def dump(self, text=""):

        print "\nState of InMemoryRecordSetConduit (%s):" % text
        for path, coll in shareDict.iteritems():
            print "\nCollection:", path
            print "\n   Latest token:", coll["token"]
            for uuid, itemHistory in coll["items"].iteritems():
                print "\n   - History for item:", uuid, "\n"
                for historicToken, diff in itemHistory:
                    if diff is None:
                        print "       [%d] <Deleted>" % historicToken
                    else:
                        print "       [%d] %s" % (historicToken, diff)
