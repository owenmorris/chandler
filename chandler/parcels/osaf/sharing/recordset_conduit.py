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
    'DiffRecordSetConduit',
    'ResourceRecordSetConduit',
    'InMemoryDiffRecordSetConduit',
    'InMemoryResourceRecordSetConduit',
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

        if self.share.established:
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

            inbound, extra, isDiff = self.getRecords(debug=debug)
            if debug: print "Inbound records", inbound, extra

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
            for uuid in inbound.keys():
                rs = inbound[uuid]
                if rs is None: # skip deletions
                    if debug: print "Inbound removal:", uuid
                    del inbound[uuid]
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
                            # as the new inbound
                            state = self.getState(uuid)
                            rs = state.agreed + state.pending + rs
                            if debug: print "Reconstituting from state:", rs
                            inbound[uuid] = rs
                            state.clear()


        else:
            inbound = {}
            isDiff = True


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

        for uuid in set(rsNewBase) | set(inbound):
            state = self.getState(uuid)
            rsInternal = rsNewBase.get(uuid, eim.RecordSet())

            if not isDiff:
                # Ensure rsExternal is the whole state
                if not inbound.has_key(uuid): # Not remotely changed
                    rsExternal = state.agreed + state.pending
                else:
                    rsExternal = inbound.get(uuid)
            else:
                rsExternal = inbound.get(uuid, eim.RecordSet())

            dSend, dApply, pending = state.merge(rsInternal, rsExternal,
                isDiff=isDiff, send=send, receive=receive, filter=filter,
                debug=debug)
            if send and dSend:
                toSend[uuid] = dSend
                logger.debug("Sending changes for %s [%s]", uuid, dSend)
                if uuid not in sendStats['added']:
                    sendStats['modified'].add(uuid)

            if receive and dApply:
                toApply[uuid] = dApply


        if receive:

            # Apply
            for uuid, rs in toApply.items():
                if debug: print "Applying:", uuid, rs
                logger.debug("Applying changes to %s [%s]", uuid, rs)
                translator.importRecords(rs)
                if uuid in remotelyAdded:
                    receiveStats['added'].add(uuid)
                else:
                    receiveStats['modified'].add(uuid)


            # Make sure any items that came in are added to the collection
            for uuid in inbound:
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
        statesToRemove = set()
        for state in self.share.states:
            uuid = self.share.states.getAlias(state)
            item = rv.findUUID(uuid)
            if (item is None or
                item not in self.share.contents and
                uuid not in remotelyRemoved):
                if send:
                    toSend[uuid] = None
                    sendStats['removed'].add(uuid)
                statesToRemove.add(uuid)
                if debug: print "Remotely removing item:", uuid



        # Send
        if send and toSend:
            extra = { 'rootName' : 'collection',
                      'uuid' : self.share.contents.itsUUID.str16(),
                      'name' : self.share.contents.displayName
                    }
            self.putRecords(toSend, extra, debug=debug)
        else:
            if debug: print "Nothing to send"
            logger.debug("Nothing to send")


        for uuid in statesToRemove:
            if debug: print "REMOVING STATE", uuid
            self.removeState(uuid)
            item = rv.findUUID(uuid)
            self.share.removeSharedItem(item)

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

    def getRecords(self, debug=False):
        raise NotImplementedError

    def putRecords(self, toSend, debug=False):
        raise NotImplementedError

    def fileStyle(self):
        return formats.STYLE_DIRECTORY

class DiffRecordSetConduit(RecordSetConduit):

    def getRecords(self, debug=False):
        text = self.get()
        if debug: print "Inbound text:", text
        logger.debug("Received from server [%s]", text)

        inbound, extra = self.serializer.deserialize(text)
        return inbound, extra, True

    def putRecords(self, toSend, extra, debug=False):
        text = self.serializer.serialize(toSend, **extra)
        if debug: print "Sending text:", text
        logger.debug("Sending to server [%s]", text)
        self.put(text)



class ResourceRecordSetConduit(RecordSetConduit):

    def getRecords(self, debug=False):
        # Get and return records, extra

        inbound = { }
        extra = { }

        # get list of remote items, store in dict keyed on path, value = etag
        self.resources = self.getResources()

        # If one of our local states isn't in the resource list, that means
        # it's been removed from the server:
        paths = { }
        for state in self.share.states:
            if hasattr(state, 'path'):
                uuid = self.share.states.getAlias(state)
                if state.path not in self.resources:
                    inbound[uuid] = None # indicator of remote deletion
                else:
                    paths[state.path] = (uuid, state)

        # Examine old and new etags to see what needs to be fetched:
        toFetch = set()
        for path, etag in self.resources.iteritems():
            if path in paths:
                state = paths[path][1]
                if etag != state.etag:
                    # Need to fetch this path since its etag doesn't match
                    if debug: print "need to fetch: etag mismatch for %s (%s vs %s)" % (path, state.etag, etag)
                    toFetch.add(path)
            else:
                # Need to fetch this path since we don't yet have it
                if debug: print "need to fetch: don't yet have %s" % path
                toFetch.add(path)

        if debug: print "%d resources to get" % len(toFetch)

        for path in toFetch:
            text, etag = self.getResource(path)
            records, extra = self.serializer.deserialize(text)
            for uuid, rs in records.iteritems():
                inbound[uuid] = rs
                state = self.getState(uuid)
                state.path = path
                state.etag = etag

        return inbound, extra, False


    def putRecords(self, toSend, extra, debug=False):

        if debug: print "putRecords [%s]" % toSend

        for uuid, rs in toSend.iteritems():
            state = self.getState(uuid)
            path = getattr(state, "path", None)
            etag = getattr(state, "etag", None)

            if rs is None:
                # delete the resource
                if path:
                    self.deleteResource(path, etag)
                    if debug: print "Deleting path %s", path
            else:
                if not path:
                    # need to compute a path
                    path = uuid

                # rs needs to include the entire recordset, not diffs
                rs = state.agreed + state.pending

                text = self.serializer.serialize({uuid : rs}, **extra)
                etag = self.putResource(text, path, etag, debug=debug)
                state.path = path
                state.etag = etag
                if debug: print "Put path %s, etag now %s [%s]" % (path,
                    etag, text)


    def newState(self, uuidString):
        state = ResourceState(itsView=self.itsView, peer=self.share,
            itemUUID=uuidString)
        self.share.states.append(state, uuidString)
        return state




class ResourceState(shares.State):
    path = schema.One(schema.Text)
    etag = schema.One(schema.Text)






shareDict = { }

class InMemoryDiffRecordSetConduit(DiffRecordSetConduit):

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

        print "\nState of InMemoryDiffRecordSetConduit (%s):" % text
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






class InMemoryResourceRecordSetConduit(ResourceRecordSetConduit):

    def getResource(self, path):
        coll = self._getCollection()
        if coll['resources'].has_key(path):
            text, etag = coll['resources'][path]
            return text, str(etag)

    def putResource(self, text, path, etag=None, debug=False):
        if etag is None:
            etag = 0
        else:
            etag = int(etag)

        coll = self._getCollection()
        if coll['resources'].has_key(path):
            oldText, oldTag = coll['resources'][path]
            if etag != oldTag:
                raise errors.TokenMismatch("Mismatched etags on PUT")
        coll['etag'] += 1
        coll['resources'][path] = (text, coll['etag'])
        if debug: print "Put [%s]" % text
        return str(coll['etag'])

    def deleteResource(self, path, etag=None):
        if etag is None:
            etag = 0
        else:
            etag = int(etag)

        coll = self._getCollection()
        if coll['resources'].has_key(path):
            oldText, oldTag = coll['resources'][path]
            if etag != oldTag:
                raise errors.TokenMismatch("Mismatched etags on DELETE")
            else:
                del coll['resources'][path]

    def exists(self):
        return shareDict.has_key(self.shareName)

    def destroy(self):
        del shareDict[self.shareName]

    def create(self):
        self._getCollection()

    def getResources(self):
        resources = { }

        coll = self._getCollection()
        for path, (text, etag) in coll['resources'].iteritems():
            resources[path] = str(etag)

        return resources

    def _getCollection(self):
        return shareDict.setdefault(self.shareName,
            { "etag" : 0, "resources" : {} })
