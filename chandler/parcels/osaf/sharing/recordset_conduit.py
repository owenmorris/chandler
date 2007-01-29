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
import conduits, errors, formats, eim, shares, merging
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
    filters = schema.Sequence(schema.Text)
    baseline = schema.One(schema.ItemRef)

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):

        if debug: print " ================ start of sync ================= "

        rv = self.itsView

        # Set up baseline if it doesn't exist
        baseline = getattr(self, 'baseline', None)
        if not baseline:
            self.baseline = shares.Baseline('baseline', self,
                peer=self.share.itsUUID.str16())

        translator = self.translator(rv)

        if self.share.contents is None:
            col = pim.SmartCollection(itsView=rv, displayName="Untitled")
            shares.SharedItem(col).add()
            self.share.contents = col

        if self.syncToken:
            version = self.itemsMarker.itsVersion
        else:
            version = -1

        # Get inbound changes
        text = self.get()
        if debug: print "Inbound text:", text

        inboundDiff, extra = self.serializer.deserialize(text)
        if debug: print "Inbound records", inboundDiff, extra

        name = extra.get('name', None)
        if name:
            self.share.contents.displayName = name


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
                shares.removeState(self.baseline, uuid)

            else:
                if debug: print "Inbound modification:", uuid
                item = rv.findUUID(uuid)
                if item is not None and item.isLive():
                    # An inbound modification to an item we already have
                    localItems.add(uuid)

                elif shares.hasState(self.baseline, uuid):
                    # This is an item we completely deleted since our last
                    # sync.  We need to grab its previous state out of the
                    # baseline, apply any pending changes and the new
                    # inbound chagnes to it, and use that as the new
                    # inboundDiff
                    agreed, pending = shares.getState(self.baseline, uuid)
                    rs = agreed + pending + rs
                    if debug: print "Reconstituting item from baseline:", rs
                    inboundDiff[uuid] = rs
                    shares.removeState(self.baseline, uuid)


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
                self.share.addSharedItem(item, baseline=self.baseline)
            else:
                rs = eim.RecordSet()
            rsNewBase[uuid] = rs


        filterUris = getattr(self, "filters", None)
        if filterUris:
            filter = merging.getFilter(filterUris)
        else:
            filter = None



        # Merge
        toSend, toApply, pending = merging.merge(self.baseline, rsNewBase,
            inboundDiff, filter=filter, debug=debug)



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
                self.share.addSharedItem(item, baseline=self.baseline)


        # For each item that was in the collection before but is no longer,
        # add an empty recordset to toSend
        for uuid in shares.getBaselineUuids(self.baseline):
            item = rv.findUUID(uuid)
            if (item is None or
                item not in self.share.contents and
                uuid not in remotelyRemoved):
                toSend[uuid] = None
                shares.removeState(self.baseline, uuid)
                if debug: print "Remotely removing item:", uuid
                self.share.removeSharedItem(item, baseline=self.baseline)


        # For each remote removal, remove the item from the collection locally
        # At this point, we know there were no local modifications
        for uuid in remotelyRemoved:
            item = rv.findUUID(uuid)
            if item is not None and item in self.share.contents:
                self.share.contents.remove(item)
                shares.removeState(self.baseline, uuid)
                if debug: print "Locally removing item:", uuid
                self.share.removeSharedItem(item, baseline=self.baseline)


        # Send
        if toSend:
            text = self.serializer.serialize(toSend, rootName="collection")
            self.put(text)
            if debug: print "Sent text:", text
        else:
            if debug: print "Nothing to send"


        # Note the repository version number, which will increase at the next
        # commit
        self.itemsMarker.setDirty(Item.NDIRTY)

        self.share.established = True

        if debug: print " ================== end of sync ================= "



    def getFilter(self):
        filter = eim.Filter(None, u'Temporary filter')
        for uri in getattr(self, 'filters', []):
            filter += eim.lookupSchemaURI(uri)
        return filter



    def saveState(self, uuidString, agreed, new_pending):
        return shares.saveState(self.baseline, uuidString, agreed,
            new_pending)

    def getState(self, uuidString):
        return shares.getState(self.baseline, uuidString)

    def discardPending(self, uuidString):
        return shares.discardPending(self.baseline, uuidString)











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


        text = self.serializer.serialize(recordsets, rootName="collection")

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
