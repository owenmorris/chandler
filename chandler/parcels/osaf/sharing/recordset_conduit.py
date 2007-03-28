#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
from osaf.activity import Activity
import conduits, errors, formats, eim, shares
from i18n import ChandlerMessageFactory as _
import logging
from application import schema
import zanshin
from repository.item.Item import Item
from chandlerdb.util.c import UUID

logger = logging.getLogger(__name__)


__all__ = [
    'RecordSetConduit',
    'DiffRecordSetConduit',
    'MonolithicRecordSetConduit',
    'ResourceRecordSetConduit',
    'InMemoryDiffRecordSetConduit',
    'InMemoryMonolithicRecordSetConduit',
    'InMemoryResourceRecordSetConduit',
]


recordset_debugging = False


class RecordSetConduit(conduits.BaseConduit):

    translator = schema.One(schema.Class)
    serializer = schema.One(schema.Class)
    syncToken = schema.One(schema.Text, defaultValue="")
    filters = schema.Many(schema.Text, initialValue=set())

    def sync(self, modeOverride=None, activity=None, forceUpdate=None,
        debug=False):

        debug = recordset_debugging or debug

        rv = self.itsView

        try:
            stats = self._sync(modeOverride=modeOverride,
                activity=activity, forceUpdate=forceUpdate,
                debug=debug)

            if activity:
                activity.update(msg="Saving...", totalWork=None)
            rv.commit() # TODO: repo merge function here?

        except Exception, exception:
            logger.exception("Sharing Error")
            rv.cancel() # Discard any changes we made
            raise

        return stats


    def _sync(self, modeOverride=None, activity=None, forceUpdate=None,
        debug=False):

        # TODO: handle mode=get
        # TODO: private items

        def _callback(*args, **kwds):
            if activity:
                activity.update(*args, **kwds)

        if debug: print " ================ start of sync ================= "

        rv = self.itsView

        stats = []
        receiveStats = { 'share' : self.share.itsUUID, 'op' : 'get',
            'added' : set(), 'modified' : set(), 'removed' : set() }
        sendStats = { 'share' : self.share.itsUUID, 'op' : 'put',
            'added' : set(), 'modified' : set(), 'removed' : set() }

        if modeOverride:
            if modeOverride == 'put':
                send = True
                receive = False
            else: # get
                send = False
                receive = True
        else:
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

        remotelyRemoved = set() # The aliases of remotely removed items
        remotelyAdded = set() # The aliases of remotely added items
        localItems = set() # The aliases of all items we're to process

        if receive:

            _callback(msg="Fetching changes", totalWork=None)
            inbound, extra, isDiff = self.getRecords(debug=debug, activity=
                activity)
            if debug: print "Inbound records", inbound, extra

            inboundCount = len(inbound)
            _callback(msg="Received %d change(s)" % inboundCount)

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
            for alias in inbound.keys():
                rs = inbound[alias]
                if rs is None: # skip deletions
                    if debug: print "Inbound removal:", alias
                    del inbound[alias]
                    remotelyRemoved.add(alias)

                    # Clear out the agreed state and any pending changes, so
                    # that if there are local changes, they'll just get sent
                    # back out along with the *complete* state of the item. The
                    # item has already been removed from the server, and we're
                    # putting it back.
                    self.removeState(alias)

                else:
                    if debug: print "Inbound modification:", alias
                    uuid = translator.getUUIDForAlias(alias)
                    if uuid:
                        item = rv.findUUID(uuid)
                    else:
                        item = None

                    if item is not None and item.isLive():
                        # An inbound modification to an item we already have
                        localItems.add(alias)

                    else:
                        remotelyAdded.add(alias)
                        if self.hasState(alias):
                            # This is an item we completely deleted since our
                            # last sync.  We need to grab its previous state
                            # out of the baseline, apply any pending changes
                            # and the new inbound chagnes to it, and use that
                            # as the new inbound
                            state = self.getState(alias)
                            rs = state.agreed + state.pending + rs
                            if debug: print "Reconstituting from state:", rs
                            inbound[alias] = rs
                            state.clear()


        else:
            inbound = {}
            isDiff = True

        _callback(msg="Checking for local changes", totalWork=None)

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

        localCount = len(locallyChangedUuids)
        _callback(msg="Found %d local change(s)" % localCount)

        for changedUuid in locallyChangedUuids:
            item = rv.findUUID(changedUuid)
            if debug: print "Locally modified item", item, item.itsVersion

            alias = translator.getAliasForItem(item)
            localItems.add(alias)
            uuid = item.itsUUID.str16()
            if not self.hasState(alias):
                sendStats['added'].add(uuid) # stats use uuids, not aliases
            if alias in remotelyRemoved:
                # This remotely removed item was modified locally.
                # We are going to send the whole item back out.
                remotelyRemoved.remove(alias)

        localCount = len(localItems)
        if localCount:
            _callback(msg="%d recordset(s) to generate" % localCount,
                totalWork=localCount, workDone=0)

        # Compute local records
        rsNewBase = { }
        i = 0
        for alias in localItems:
            uuid = translator.getUUIDForAlias(alias)
            if uuid:
                item = rv.findUUID(uuid)
            else:
                item = None

            if item is not None and item.isLive():
                rs = eim.RecordSet(translator.exportItem(item))
                self.share.addSharedItem(item)
                if debug: print "Computing local records for live item:", uuid
            else:
                rs = eim.RecordSet()
                if debug: print "No local item for:", uuid
            rsNewBase[alias] = rs
            i += 1
            _callback(msg="Generated %d of %d recordset(s)" % (i, localCount),
                work=1)


        filter = self.getFilter()

        # Merge
        toApply = {}
        toSend = {}

        aliases = set(rsNewBase) | set(inbound)
        mergeCount = len(aliases)
        if mergeCount:
            _callback(msg="%d recordset(s) to merge" % mergeCount,
                totalWork=mergeCount, workDone=0)

        i = 0
        for alias in aliases:
            state = self.getState(alias)
            rsInternal = rsNewBase.get(alias, eim.RecordSet())

            if not isDiff:
                # Ensure rsExternal is the whole state
                if not inbound.has_key(alias): # Not remotely changed
                    rsExternal = state.agreed + state.pending
                else:
                    rsExternal = inbound.get(alias)
            else:
                rsExternal = inbound.get(alias, eim.RecordSet())

            dSend, dApply, pending = state.merge(rsInternal, rsExternal,
                isDiff=isDiff, filter=filter, debug=debug)

            uuid = translator.getUUIDForAlias(alias)
            if uuid:
                item = rv.findUUID(uuid)
            else:
                item = None
            state.updateConflicts(item)

            if send and dSend:
                toSend[alias] = dSend
                logger.debug("Sending changes for %s [%s]", alias, dSend)
                if uuid not in sendStats['added']:
                    sendStats['modified'].add(uuid)

            if receive and dApply:
                toApply[alias] = dApply

            i += 1
            _callback(msg="Merged %d of %d recordset(s)" % (i, mergeCount),
                work=1)

        if receive:

            applyCount = len(toApply)
            if applyCount:
                _callback(msg="%d inbound change(s) to apply" % applyCount,
                    totalWork=applyCount, workDone=0)

            # Apply
            i = 0
            for alias, rs in toApply.items():
                if debug: print "Applying:", alias, rs
                logger.debug("Applying changes to %s [%s]", alias, rs)

                uuid = translator.getUUIDForAlias(alias)
                if uuid:
                    item = rv.findUUID(uuid)
                else:
                    item = None

                # Mark existing items as "unread" now, so that importing can
                # override it (if we're reloading, f'rinstance)
                if item is not None:
                    item.read = False

                translator.importRecords(rs)

                uuid = translator.getUUIDForAlias(alias)
                if uuid:
                    item = rv.findUUID(uuid)
                else:
                    item = None

                # Set triage status, based on the values we loaded
                if item is not None:
                    item.setTriageStatus('auto', popToNow=True)

                if alias in remotelyAdded:
                    receiveStats['added'].add(uuid)
                else:
                    receiveStats['modified'].add(uuid)
                i += 1
                _callback(msg="Applied %d of %d change(s)" % (i, applyCount),
                    work=1)


            # Make sure any items that came in are added to the collection
            for alias in inbound:
                uuid = translator.getUUIDForAlias(alias)
                if uuid:
                    item = rv.findUUID(uuid)
                else:
                    item = None

                # Add the item to contents
                if item is not None and item.isLive():
                    if debug: print "Adding to collection:", uuid
                    self.share.contents.add(item)
                    self.share.addSharedItem(item)


            # For each remote removal, remove the item from the collection
            # locally
            # At this point, we know there were no local modifications
            for alias in remotelyRemoved:
                uuid = translator.getUUIDForAlias(alias)
                if uuid:
                    item = rv.findUUID(uuid)
                else:
                    item = None

                if item is not None and item in self.share.contents:
                    self.share.contents.remove(item)
                    self.removeState(alias)
                    self.share.removeSharedItem(item)
                    receiveStats['removed'].add(uuid)
                    if debug: print "Locally removing item:", uuid



        # For each item that was in the collection before but is no longer,
        # remove its state; if sending, add an empty recordset to toSend
        # TODO: Optimize by removing item loading
        statesToRemove = set()
        for state in self.share.states:
            alias = self.share.states.getAlias(state)
            uuid = translator.getUUIDForAlias(alias)
            if uuid:
                item = rv.findUUID(uuid)
            else:
                item = None

            if (item is None or
                item not in self.share.contents and
                alias not in remotelyRemoved):
                if send:
                    toSend[alias] = None
                    sendStats['removed'].add(uuid)
                statesToRemove.add(alias)
                if debug: print "Remotely removing item:", alias

        removeCount = len(statesToRemove)
        if removeCount:
            _callback(msg="%d local removal(s) detected" % removeCount,
                totalWork=None)


        # Send
        if send and toSend:
            sendCount = len(toSend)
            _callback(msg="Sending %d outbound change(s)" % sendCount,
                totalWork=None)

            extra = { 'rootName' : 'collection',
                      'uuid' : self.share.contents.itsUUID.str16(),
                      'name' : self.share.contents.displayName
                    }
            self.putRecords(toSend, extra, debug=debug, activity=activity)
        else:
            if debug: print "Nothing to send"
            logger.debug("Nothing to send")


        for alias in statesToRemove:
            if debug: print "REMOVING STATE", alias
            self.removeState(alias)
            uuid = translator.getUUIDForAlias(alias)
            if uuid:
                item = rv.findUUID(uuid)
                if item is not None:
                    self.share.removeSharedItem(item)

        # Note the repository version number, which will increase at the next
        # commit
        self.itemsMarker.setDirty(Item.NDIRTY)

        self.share.established = True

        _callback(msg="Done")

        if debug: print " ================== end of sync ================= "

        if receive:
            receiveStats['applied'] = toApply
            stats.append(receiveStats)
        if send:
            sendStats['sent'] = toSend
            stats.append(sendStats)
        return stats




    def getState(self, alias):
        state = self.share.states.getByAlias(alias)
        if state is None:
            state = self.newState(alias)
        return state

    def newState(self, alias):
        state = shares.State(itsView=self.itsView, peer=self.share)
        self.share.states.append(state, alias)
        return state

    def removeState(self, alias):
        state = self.share.states.getByAlias(alias)
        if state is not None:
            self.share.states.remove(state)
            state.delete(True)

    def hasState(self, alias):
        return self.share.states.getByAlias(alias) is not None


    def getFilter(self):
        filter = eim.Filter(None, u'Temporary filter')
        for uri in getattr(self, 'filters', []):
            filter += eim.lookupSchemaURI(uri)
        return filter

    def getRecords(self, debug=False, activity=None):
        raise NotImplementedError

    def putRecords(self, toSend, extra, debug=False, activity=None):
        raise NotImplementedError

    def fileStyle(self):
        return formats.STYLE_DIRECTORY




class DiffRecordSetConduit(RecordSetConduit):

    def getRecords(self, debug=False, activity=None):
        text = self.get()
        if debug: print "Inbound text:", text
        logger.debug("Received from server [%s]", text)

        inbound, extra = self.serializer.deserialize(text)
        return inbound, extra, True

    def putRecords(self, toSend, extra, debug=False, activity=None):
        text = self.serializer.serialize(toSend, **extra)
        if debug: print "Sending text:", text
        logger.debug("Sending to server [%s]", text)
        self.put(text)





class MonolithicRecordSetConduit(RecordSetConduit):

    etag = schema.One(schema.Text, initialValue="")

    def getRecords(self, debug=False, activity=None):
        text = self.get()
        if debug: print "Inbound text:", text
        logger.debug("Received from server [%s]", text)

        if text:
            inbound, extra = self.serializer.deserialize(text)
            return inbound, extra, False
        else:
            return { }, { }, False

    def putRecords(self, toSend, extra, debug=False, activity=None):
        # get the full state of every item not being deleted
        fullToSend = { }
        for state in self.share.states:
            alias = self.share.states.getAlias(state)
            if toSend.has_key(alias) and toSend[alias] is None:
                pass
            else:
                rs = state.agreed + state.pending
                fullToSend[alias] = rs

        text = self.serializer.serialize(fullToSend, **extra)
        if debug: print "Sending text:", text
        logger.debug("Sending to server [%s]", text)
        self.put(text)

    def fileStyle(self):
        return formats.STYLE_SINGLE





class ResourceRecordSetConduit(RecordSetConduit):

    def getRecords(self, debug=False, activity=None):
        # Get and return records, extra

        inbound = { }
        extra = { }

        # get list of remote items, store in dict keyed on path, value = etag
        if activity:
            activity.update(msg="Getting list of resources", totalWork=None)
        self.resources = self.getResources()

        # If one of our local states isn't in the resource list, that means
        # it's been removed from the server:
        paths = { }
        for state in self.share.states:
            if hasattr(state, 'path'):
                alias = self.share.states.getAlias(state)
                if state.path not in self.resources:
                    inbound[alias] = None # indicator of remote deletion
                else:
                    paths[state.path] = (alias, state)

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

        fetchCount = len(toFetch)
        if debug: print "%d resources to get" % fetchCount
        if activity:
            activity.update(msg="%d resources to get" % fetchCount,
                totalWork=fetchCount, workDone=0)

        i = 0
        for path in toFetch:
            if activity:
                i += 1
                activity.update(msg="Getting %d of %d" % (i, fetchCount),
                    work=1)
            text, etag = self.getResource(path)
            if debug: print "Inbound text:", text
            records, extra = self.serializer.deserialize(text)
            for alias, rs in records.iteritems():
                inbound[alias] = rs
                state = self.getState(alias)
                state.path = path
                state.etag = etag

        return inbound, extra, False


    def putRecords(self, toSend, extra, debug=False, activity=None):

        sendCount = len(toSend)

        if activity:
            activity.update(msg="Sending %d resources" % sendCount,
                totalWork=sendCount, workDone=0)

        i = 0
        for alias, rs in toSend.iteritems():
            state = self.getState(alias)
            path = getattr(state, "path", None)
            etag = getattr(state, "etag", None)

            if activity:
                i += 1
                activity.update(msg="Sending %d of %d" % (i, sendCount),
                    work=1)

            if rs is None:
                # delete the resource
                if path:
                    self.deleteResource(path, etag)
                    if debug: print "Deleting path %s", path
            else:
                if not path:
                    # need to compute a path
                    path = self.getPath(UUID().str16())

                # rs needs to include the entire recordset, not diffs
                rs = state.agreed + state.pending

                if debug: print "Full resource records:", rs

                text = self.serializer.serialize({alias : rs}, **extra)
                if debug: print "Sending text:", text
                etag = self.putResource(text, path, etag, debug=debug)
                state.path = path
                state.etag = etag
                if debug: print "Put path %s, etag now %s" % (path, etag)


    def newState(self, alias):
        state = ResourceState(itsView=self.itsView, peer=self.share)
        self.share.states.append(state, alias)
        return state


    def getPath(self, uuid):
        return uuid


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




class InMemoryMonolithicRecordSetConduit(MonolithicRecordSetConduit):

    def get(self):
        self.etag, text = self.serverGet(self._getPath(), self.etag)
        return text

    def put(self, text):
        self.etag = self.serverPut(self._getPath(), text, self.etag)

    def exists(self):
        return shareDict.has_key(self._getPath())

    def destroy(self):
        del shareDict[self._getPath()]

    def create(self):
        self._getCollection(self._getPath())

    def _getPath(self):
        return "/".join([self.sharePath, self.shareName])

    def _getCollection(self, path):
        return shareDict.setdefault(path, { "etag" : 0, "text" : None })


    def serverPut(self, path, text, etag):
        if etag:
            etag = int(etag)
        else:
            etag = 0

        coll = self._getCollection(path)
        current = coll["etag"]
        if current > etag:
            raise errors.TokenMismatch("Remote content has been updated")

        coll["text"] = text
        current += 1
        coll["etag"] = current
        return str(current)


    def serverGet(self, path, etag):

        if etag:
            etag = int(etag)
        else:
            etag = 0

        coll = self._getCollection(path)

        current = coll["etag"]
        if etag >= current:
            # content not modified
            return str(current), None

        return str(current), coll["text"]








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


