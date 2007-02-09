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
import conduits, errors, formats, eim, shares
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



class RecordSetConduit(conduits.BaseConduit):

    translator = schema.One(schema.Class)
    serializer = schema.One(schema.Class)
    syncToken = schema.One(schema.Text, defaultValue="")
    filters = schema.Many(schema.Text, initialValue=set())

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):

        rv = self.itsView

        try:
            stats = self._sync(modeOverride=modeOverride,
                updateCallback=updateCallback, forceUpdate=forceUpdate,
                debug=debug)

            rv.commit() # TODO: repo merge function here?

        except:
            logger.exception("Sharing Error")
            rv.cancel() # Discard any changes we made
            raise

        return stats


    def _sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):

        # TODO: handle mode=get
        # TODO: private items

        if debug: print " ================ start of sync ================= "

        rv = self.itsView

        stats = []
        receiveStats = { 'share' : self.share.itsUUID, 'op' : 'get',
            'added' : set(), 'modified' : set(), 'removed' : set() }
        sendStats = { 'share' : self.share.itsUUID, 'op' : 'put',
            'added' : set(), 'modified' : set(), 'removed' : set() }

        send = self.share.mode in ('put', 'both')
        receive = self.share.mode in ('get', 'both')

        translator = self.translator(rv)

        if self.syncToken:
            version = self.itemsMarker.itsVersion
        else:
            version = 0
            # This is our first sync; if we're already assigned a collection,
            # that means this is our initial publish; don't receive
            if self.share.contents is not None:
                receive = False

        remotelyRemoved = set() # The uuids of remotely removed items
        remotelyAdded = set() # The uuids of remotely added items
        localItems = set() # The uuids of all items we're to process

        if receive:

            text = self.get()
            if debug: print "Inbound text:", text

            inboundDiff, extra = self.serializer.deserialize(text)
            if debug: print "Inbound records", inboundDiff, extra

            if self.share.contents is None:
                # We're importing a collection; either create it if it
                # doesn't exist, or grab the matching one we already have.
                collectionUuid = extra.get('uuid', None)
                if collectionUuid:
                    collection = translator.loadItemByUUID(collectionUuid,
                        pim.SmartCollection)
                else:
                    # We weren't provided a collection, so let's create our
                    # own
                    collection = pim.SmartCollection(itsView=rv,
                        displayName="Untitled")

                if not pim.has_stamp(collection, shares.SharedItem):
                    shares.SharedItem(collection).add()

                self.share.contents = collection

            # If the inbound collection name is provided we change the local
            # collection name
            name = extra.get('name', None)
            if name:
                self.share.contents.displayName = name

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

                    else:
                        remotelyAdded.add(uuid)
                        if self.hasState(uuid):
                            # This is an item we completely deleted since our
                            # last sync.  We need to grab its previous state
                            # out of the baseline, apply any pending changes
                            # and the new inbound chagnes to it, and use that
                            # as the new inboundDiff
                            state = self.getState(uuid)
                            rs = state.agreed + state.pending + rs
                            if debug: print "Reconstituting from state:", rs
                            inboundDiff[uuid] = rs
                            self.removeState(uuid)


        else:
            inboundDiff = {}


        # Generate records for all local items to be merged -- those that
        # have either been changed locally or remotely:

        if debug: print "Conduit marker version:", version

        # Add locally changed items
        locallyChangedUuids = set()

        if forceUpdate:
            # A filter was changed, so we need to publish all items again
            for item in self.share.contents:
                locallyChangedUuids.add(item.itsUUID)

        else:
            # This loop tries to avoid loading any non-dirty items:
            # When statistics logging is added, we can verify this loop is doing
            # what we expect
            for change in rv.mapHistory(version):
                changedUuid = change[0]
                if changedUuid in self.share.contents:
                    locallyChangedUuids.add(changedUuid)

        for changedUuid in locallyChangedUuids:
                item = rv.findUUID(changedUuid)
                if debug: print "Locally modified item", item, item.itsVersion

                # If an event, make sure we export the master; occurrences
                # will be included in the master's recordset
                if pim.has_stamp(item, pim.EventStamp):
                    item = pim.EventStamp(item).getMaster().itsItem
                    if debug: print "Master item", item, item.itsVersion

                uuid = item.itsUUID.str16()
                localItems.add(uuid)
                if not self.hasState(uuid):
                    sendStats['added'].add(uuid)
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
                self.share.addSharedItem(item)
                if debug: print "Computing local records for live item:", uuid
            else:
                rs = eim.RecordSet()
                if debug: print "No local item for:", uuid
            rsNewBase[uuid] = rs



        filter = self.getFilter()

        # Merge
        toApply = {}
        toSend = {}

        for uuid in set(rsNewBase) | set(inboundDiff):
            state = self.getState(uuid)
            rsInternal = rsNewBase.get(uuid, eim.RecordSet())
            rsExternal = inboundDiff.get(uuid, eim.RecordSet())
            dSend, dApply, pending = state.merge(rsInternal, rsExternal,
                send=send, receive=receive, filter=filter, debug=debug)
            if send and dSend:
                toSend[uuid] = dSend
                if uuid not in sendStats['added']:
                    sendStats['modified'].add(uuid)
            if receive and dApply:
                toApply[uuid] = dApply


        if receive:

            # Apply
            for uuid, rs in toApply.items():
                if debug: print "Applying:", uuid, rs
                translator.importRecords(rs)
                if uuid in remotelyAdded:
                    receiveStats['added'].add(uuid)
                else:
                    receiveStats['modified'].add(uuid)


            # Make sure any items that came in are added to the collection
            for uuid in inboundDiff:
                # Add the item to contents
                item = rv.findUUID(uuid)
                if item is not None and item.isLive():
                    if debug: print "Adding to collection:", uuid
                    self.share.contents.add(item)
                    self.share.addSharedItem(item)


            # For each remote removal, remove the item from the collection
            # locally
            # At this point, we know there were no local modifications
            for uuid in remotelyRemoved:
                item = rv.findUUID(uuid)
                if item is not None and item in self.share.contents:
                    self.share.contents.remove(item)
                    self.removeState(uuid)
                    self.share.removeSharedItem(item)
                    receiveStats['removed'].add(uuid)
                    if debug: print "Locally removing item:", uuid



        # For each item that was in the collection before but is no longer,
        # remove its state; if sending, add an empty recordset to toSend
        # TODO: Optimize by removing item loading
        for state in self.share.states:
            uuid = self.share.states.getAlias(state)
            item = rv.findUUID(uuid)
            if (item is None or
                item not in self.share.contents and
                uuid not in remotelyRemoved):
                if send:
                    toSend[uuid] = None
                    sendStats['removed'].add(uuid)
                self.removeState(uuid)
                self.share.removeSharedItem(item)
                if debug: print "Remotely removing item:", uuid



        # Send
        if send and toSend:
            # TODO: send the real collection's uuid
            text = self.serializer.serialize(toSend, rootName="collection",
                uuid=self.share.contents.itsUUID.str16())
            if debug: print "Sending text:", text
            self.put(text)
        else:
            if debug: print "Nothing to send"


        # Note the repository version number, which will increase at the next
        # commit
        self.itemsMarker.setDirty(Item.NDIRTY)

        self.share.established = True

        if debug: print " ================== end of sync ================= "

        if receive:
            receiveStats['applied'] = toApply
            stats.append(receiveStats)
        if send:
            sendStats['sent'] = toSend
            stats.append(sendStats)
        return stats




    def getState(self, uuidString):
        state = self.share.states.getByAlias(uuidString)
        if state is None:
            state = self.newState(uuidString)
        return state

    def newState(self, uuidString):
        state = shares.State(itsView=self.itsView, peer=self.share,
            itemUUID=uuidString)
        self.share.states.append(state, uuidString)
        return state

    def removeState(self, uuidString):
        state = self.share.states.getByAlias(uuidString)
        if state is not None:
            self.share.states.remove(state)
            state.delete(True)

    def hasState(self, uuidString):
        return self.share.states.getByAlias(uuidString) is not None


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
        recordsets, extra = self.serializer.deserialize(text)
        coll = self._getCollection(path)
        if extra.has_key("name"):
            coll["name"] = extra["name"]
        if extra.has_key("uuid"):
            coll["uuid"] = extra["uuid"]
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


        extra = { }
        if coll.has_key("uuid"): extra["uuid"] = coll["uuid"]
        if coll.has_key("name"): extra["name"] = coll["name"]
        text = self.serializer.serialize(recordsets, rootName="collection",
            **extra)

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
