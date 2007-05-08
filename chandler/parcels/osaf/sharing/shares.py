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
__all__ = [
    'OneTimeShare',
    'OneTimeFileSystemShare',
    'Share',
    'SharedItem',
    'State',
    'Conflict',
    'getFilter',
    'hasConflicts',
    'getConflicts',
]

from application import schema
from osaf import pim
import errors, eim, model
from eim import NoChange as nc
from callbacks import *
import cPickle
import logging
import datetime
from PyICU import ICUtzinfo
from chandlerdb.util.c import Empty

logger = logging.getLogger(__name__)






class SharedItem(pim.Stamp):
    schema.kindInfo(annotates=pim.ContentItem)

    shares = schema.Sequence(initialValue=[])
    # 'shares' is used to link collection to their shares

    sharedIn = schema.Sequence(initialValue=[])
    # 'sharedIn' links shared items to their shares

    peerStates = schema.Sequence()
    # 'peerStates' is used only for p2p sharing, including mail-edit-update.
    # It's a ref collection aliased by peer.itsUUID.str16()
    # In Cosmo-based sharing, states are stored in the conduit

    conflictingStates = schema.Sequence(defaultValue=Empty)

    def getConflicts(self):
        for state in self.conflictingStates:
            for conflict in state.getConflicts():
                # protect against proxies being passed in
                item = getattr(self.itsItem, 'proxiedItem', self.itsItem)
                conflict.item = item
                yield conflict


    def generateConflicts(self, **kwds):
        # TODO: replace this with something that generates more interesting
        # conflicts
        if not self.conflictingStates:
            itemUUID = self.itsItem.itsUUID.str16()
            peer = pim.EmailAddress(itsView=self.itsItem.itsView,
                emailAddress="conflict@example.com")
            state = State(itsView=self.itsItem.itsView, peer=peer)

            state.pending = eim.RecordSet([
                model.ItemRecord(itemUUID, "An alterative title", nc, nc, nc, nc, nc),
                model.NoteRecord(itemUUID, "A different note", nc, nc, nc),
                model.EventRecord(itemUUID, nc, nc, "San Jose", nc, nc, nc,
                    nc, nc),
            ])
            state.updateConflicts(self.itsItem)


    def addPeerState(self, state, peer):
        peerUuid = peer.itsUUID.str16()
        if not hasattr(self, 'peerStates'):
            self.peerStates = []
        if state not in self.peerStates:
            self.peerStates.append(state, peerUuid)

    def getPeerState(self, peer, create=True):
        peerUuid = peer.itsUUID.str16()
        state = None
        if hasattr(self, 'peerStates'):
            state = self.peerStates.getByAlias(peerUuid)
        else:
            self.peerStates = []
        if state is None and create:
            state = State(itsView=self.itsItem.itsView, peer=peer)
            self.peerStates.append(state, peerUuid)
        return state

    def removePeerState(self, peer):
        state = self.getPeerState(peer, create=False)
        if state is not None:
            self.peerStates.remove(state)
            state.delete(True)


    # In the new sharing world, this method might be obsolete, now that even
    # read-only attributes can technically be locally modified without being
    # automatically overwritten by inbound changes -- those inbound changes
    # would be held as pending conflicts.

    def isAttributeModifiable(self, attribute):

        # fast path -- item is unshared; have at it!
        if not self.sharedIn:
            return True

        # slow path -- item is shared; we need to look at all the *inbound*
        # shares this item participates in -- if *any* of those inbound shares
        # are writable, the attribute is modifiable; otherwise, if *all* of
        # those inbound shares are read-only, but none of those shares
        # actually *share* that attribute (i.e., it's being filtered either
        # by sharing cloud or explicit filter), then it's modifiable.

        for share in self.sharedIn:
            if share.isAttributeModifiable(self.itsItem, attribute):
                return True

        return False



def hasConflicts(item):
    if pim.has_stamp(item, SharedItem):
        shared = SharedItem(item)
        if shared.conflictingStates:
            return True
    return False

def getConflicts(item):
    conflicts = []
    if pim.has_stamp(item, SharedItem):
        shared = SharedItem(item)
        for conflict in shared.getConflicts():
            conflicts.append(conflict)
    return conflicts



class State(schema.Item):

    peer = schema.One(schema.ItemRef)
    peerStateFor = schema.One(inverse=SharedItem.peerStates)
    peerRepoId = schema.One(schema.Text, initialValue="")
    peerItemVersion = schema.One(schema.Integer, initialValue=-1)
    conflictFor = schema.One(inverse=SharedItem.conflictingStates)
    share = schema.One()
    conflictingShare = schema.One()

    # Internal
    _agreed = schema.One(schema.Bytes)
    _pending = schema.One(schema.Bytes)


    def __repr__(self):
        return "State(%r, %r)" % (self.agreed, self.pending)


    def getAgreed(self):
        if hasattr(self, '_agreed'):
            return cPickle.loads(self._agreed)
        else:
            return eim.RecordSet()

    def setAgreed(self, agreed):
        self._agreed = cPickle.dumps(agreed)

    def delAgreed(self):
        del self._agreed

    agreed = property(getAgreed, setAgreed, delAgreed)



    def getPending(self):
        if hasattr(self, '_pending'):
            return cPickle.loads(self._pending)
        else:
            return eim.RecordSet()

    def setPending(self, pending):
        self._pending = cPickle.dumps(pending)

    def delPending(self):
        del self._pending

    pending = property(getPending, setPending, delPending)



    def merge(self, rsInternal, inbound=eim.RecordSet(), isDiff=True,
        filter=None, readOnly=False, debug=False):

        if filter is None:
            filter = lambda rs: rs
        else:
            filter = filter.sync_filter

        pending = self.pending

        # We need to set rsExternal to equal the entire external state

        # If we're passing in a diff, apply it to agreed + pending
        if isDiff:
            rsExternal = self.agreed + pending + inbound

        else:
            rsExternal = inbound

        internalDiff = filter(rsInternal - self.agreed)
        externalDiff = filter(rsExternal - self.agreed)
        ncd = internalDiff | externalDiff

        if debug:
            print " ----------- Beginning merge"
            print "   rsInternal:", rsInternal
            print "   internalDiff:", internalDiff
            print "   externalDiff:", externalDiff
            print "   old agreed:", self.agreed
            print "   old pending:", pending
            print "   ncd:", ncd

        if readOnly:
            # This allows a read-only subscriber to maintain local changes
            # that only conflict when someone else makes a conflicting change,
            # and not *every* time they sync.

            # We don't want internal changes from
            # reaching self.agreed or dSend.  We *do* want to be alerted to
            # conflicts between internal and external changes, however.  To
            # do this, we generate a recordset representing how things would
            # be if the external changes won, and another recordset
            # representing how things would be if the internal changes won,
            # and we diff the two.

            extWins = self.agreed + internalDiff + self.pending + externalDiff
            intWins = self.agreed + self.pending + externalDiff + internalDiff
            if debug:
                print "   extWins:", extWins
                print "   intWins:", intWins
            self.pending = filter(extWins - intWins)

            self.agreed = filter(rsExternal)
            dSend = eim.RecordSet()

        else:
            self.agreed += ncd
            dSend = self._cleanDiff(rsExternal, ncd)
            rsExternal += dSend
            self.pending = filter(rsExternal - self.agreed)

        dApply = self._cleanDiff(rsInternal, ncd)


        if debug:
            print " - - - - Results - - - - "
            print "   dSend:", dSend
            print "   dApply:", dApply
            print "   new agreed:", self.agreed
            print "   new pending:", self.pending
            print " ----------- Merge complete"

        return dSend, dApply, self.pending

    def _cleanDiff(self, state, diff):
        newState = state + diff
        newState.exclusions = set()
        diff = newState - state
        return diff

    def updateConflicts(self, item):
        # See if we have pending conflicts; if so, make sure we are in the
        # item's conflictingStates ref collection.  If not, make sure we
        # aren't.
        if item is not None:
            if not pim.has_stamp(item, SharedItem):
                SharedItem(item).add()
            shared = SharedItem(item)
            if self.pending:
                self.conflictFor = item
                if getattr(self, 'share', None):
                    self.conflictingShare = self.share
            else:
                self.conflictFor = None
                self.conflictingShare = None


    def set(self, agreed, pending):
        self.agreed = agreed
        self.pending = pending

    def clear(self):
        try:
            del self._agreed
        except AttributeError:
            pass
        try:
            del self._pending
        except AttributeError:
            pass
        self.peerItemVersion = -1

    def apply(self, change):
        translator = self.getTranslator()
        translator.startImport()
        translator.importRecords(change)
        translator.finishImport()
        self.agreed += change
        self.discard(change)

    def discard(self, change):
        pending = self.pending
        pending.remove(change)
        self.pending = pending
        self.agreed += change

    def getConflicts(self):
        if self.pending:
            for n,v,c in self.getTranslator().explainConflicts(self.pending):
                # XXX this currently converts the value to a string or unicode,
                # but in the future this should be done by formatters in the
                # EIM framework.  The "%s" craziness is a Python idiom that
                # leaves strings as strings and unicode as unicode, but
                # converts everything else to a string.
                yield Conflict(self, n, "%s" % (v,), c)

    def getTranslator(self):
        # This is so when we need multiple translator types, we'll still only
        # have one place to call to get them...
        return eim.lookupSchemaURI("cid:pim-translator@osaf.us")(self.itsView)







class Conflict(object):

    resolved = False

    def __init__(self, state, field, value, change):
        self.state = state
        self.peer = state.peer
        self.field = field
        self.value = value
        self.change = change
        self.item = None

    def __repr__(self):
        return "%s : %s" % (self.field, self.value)

    def apply(self):
        if not self.resolved:
            self.state.apply(self.change)
            self.resolved = True
            if self.item is not None:
                self.state.updateConflicts(self.item)

    def discard(self):
        if not self.resolved:
            self.state.discard(self.change)
            self.resolved = True
            if self.item is not None:
                self.state.updateConflicts(self.item)






def getFilter(filterUris):
    filter = eim.Filter(None, u'Temporary filter')
    for uri in filterUris:
        filter += eim.lookupSchemaURI(uri)
    return filter








class modeEnum(schema.Enumeration):
    values = "put", "get", "both"


class Share(pim.ContentItem):
    """
    Represents a set of shared items, encapsulating contents, location,
    access method, data format, sharer and sharees.
    """

    schema.kindInfo(
        description="Represents a shared collection",
    )

    hidden = schema.One(
        schema.Boolean,
        doc = 'This attribute is used to denote which shares have been '
              'created by the user via the detail view (hidden=False) versus '
              'those that are being created for other purposes (hidden=True), '
              'such as transient import/export shares, .ics publishing, etc.',
        initialValue = False,
    )

    active = schema.One(
        schema.Boolean,
        doc = "This attribute indicates whether this share should be synced "
              "during a 'sync all' operation.",
        initialValue = True,
    )

    established = schema.One(
        schema.Boolean,
        doc = "This attribute indicates whether the share has been "
              "successfully subscribed/published at least once.",
        initialValue = False,
    )

    mode = schema.One(
        modeEnum,
        doc = 'This attribute indicates the sync mode for the share:  '
              'get, put, or both',
        initialValue = 'both',
    )

    error = schema.One(
        schema.Text,
        doc = 'A message summarizing the last error; empty string otherwise',
        initialValue = u''
    )

    errorDetails = schema.One(
        schema.Text,
        doc = 'A message detailing the last error; empty string otherwise',
        initialValue = u''
    )

    lastAttempt = schema.One(schema.DateTimeTZ)
    lastSuccess = schema.One(schema.DateTimeTZ)
    lastStats = schema.Sequence(schema.Dictionary, initialValue=[])

    contents = schema.One(inverse=SharedItem.shares, initialValue=None)
    items = schema.Sequence(inverse=SharedItem.sharedIn, initialValue=[])

    conduit = schema.One(initialValue=None)
    # inverse of Conduit.share

    format = schema.One(initialValue=None)
    # inverse of ImportExportFormat.share

    states = schema.Sequence(State,
        inverse=State.share, initialValue=[])
    conflictingStates = schema.Sequence(State,
        inverse=State.conflictingShare, initialValue=[])

    sharer = schema.One(
        pim.Contact,
        doc = 'The contact who initially published this share',
        initialValue = None,
        inverse = schema.Sequence(),
    )

    sharees = schema.Sequence(
        pim.Contact,
        doc = 'The people who were invited to this share',
        initialValue = [],
        inverse = schema.Sequence(),
    )

    filterClasses = schema.Sequence(
        schema.Text,
        doc = 'The list of classes to import/export',
        initialValue = [],
    )

    filterAttributes = schema.Sequence(schema.Text, initialValue=[])

    leads = schema.Sequence(initialValue=[])
    follows = schema.One(inverse=leads)

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [filterAttributes],
            byCloud = [contents, sharer, sharees]
        ),
        copying = schema.Cloud(byCloud=[format, conduit])
    )


    def fileStyle(self):
        if getattr(self, "format", None) is not None:
            return self.format.fileStyle()
        else:
            return self.conduit.fileStyle()

    def addSharedItem(self, item):
        """ Add an item to the share's sharedIn refcoll, stamping if
            necessary """
        if not pim.has_stamp(item, SharedItem):
            SharedItem(item).add()
        sharedItem = SharedItem(item)
        sharedItem.sharedIn = self

    def removeSharedItem(self, item):
        """ Remove an item from the share's sharedIn refcoll, unstamping if
            the last share for this item """
        if not pim.has_stamp(item, SharedItem):
            return
        sharedItem = SharedItem(item)
        sharedItem.sharedIn.remove(self)
        if not sharedItem.sharedIn:
            SharedItem(item).remove()

    def hasConflicts(self):
        return True if self.conflictingStates else False

    def create(self):
        self.conduit.create()

    def destroy(self):
        self.conduit.destroy()

    def open(self):
        self.conduit.open()

    def close(self):
        self.conduit.close()

    def sync(self, modeOverride=None, activity=None, forceUpdate=None,
        debug=False):

        # @@@MOR: Refactor this and the conduits' sync( ) methods so that
        # only the cancel/commit happens here, once the dual-fork stuff
        # is removed.

        if(self.contents is not None and
            not pim.has_stamp(self.contents, SharedItem)):
            SharedItem(self.contents).add()

        self.lastAttempt = datetime.datetime.now(ICUtzinfo.default)

        # Clear any previous error
        for linked in self.getLinkedShares():
            if hasattr(linked, 'error'):
                del linked.error
            if hasattr(linked, 'errorDetails'):
                del linked.errorDetails

        try:
            stats = self.conduit.sync(modeOverride=modeOverride,
                                      activity=activity,
                                      forceUpdate=forceUpdate, debug=debug)

            # Not sure we need to keep the last stats around.  It's just more
            # data to persist.  If it ends up being helpful we can put it back
            # in:

            # self.lastStats = stats

            self.lastSuccess = datetime.datetime.now(ICUtzinfo.default)

        except Exception, e:

            logger.exception("Error syncing collection")

            summary, extended = errors.formatException(e)

            # At this point, our view has been cancelled.  Only 'established'
            # Share items will still be alive here, and those are precisely
            # the ones we do want to store error messages on:
            if self.isLive():
                for linked in self.getLinkedShares():
                    linked.error = summary
                    linked.errorDetails = extended

            raise

        return stats

    def put(self, activity=None, forceUpdate=None, debug=False):
        return self.sync(modeOverride='put', activity=activity,
                         forceUpdate=forceUpdate, debug=debug)

    def get(self, activity=None, debug=False):
        return self.sync(modeOverride='get', activity=activity,
                         debug=debug)

    def exists(self):
        return self.conduit.exists()

    def getLocation(self, privilege=None):
        return self.conduit.getLocation(privilege=privilege)

    def getSharedAttributes(self, kind, cloudAlias='sharing'):
        """
        Examine sharing clouds and filterAttributes to determine which
        attributes to share for a given kind
        """

        attributes = set()
        skip = getattr(self, 'filterAttributes', [])

        for cloud in kind.getClouds(cloudAlias):
            for alias, endpoint, inCloud in cloud.iterEndpoints(cloudAlias):
                # @@@MOR for now, don't support endpoint attribute 'chains'
                attrName = endpoint.attribute[0]

                # An includePolicy of 'none' is how we override an inherited
                # endpoint
                if not (endpoint.includePolicy == 'none' or
                        attrName in skip):
                    attributes.add(attrName)

        return attributes

    def getLinkedShares(self):

        def getFollowers(share):
            if hasattr(share, 'leads'):
                for follower in share.leads:
                    yield follower
                    for subfollower in getFollowers(follower):
                        yield subfollower

        # Find the root leader
        root = self
        leader = getattr(root, 'follows', None)
        while leader is not None:
            root = leader
            leader = getattr(root, 'follows', None)

        shares = [root]
        for follower in getFollowers(root):
            shares.append(follower)

        return shares

    def isAttributeModifiable(self, item, attribute):

        if hasattr(self.conduit, 'isAttributeModifiable'):
            return self.conduit.isAttributeModifiable(item, attribute)
        else:
            return True






# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =


class OneTimeShare(Share):
    """
    Delete format, conduit, and share after the first get or put.
    """

    def remove(self):
        # With deferred deletes, we need to also remove the Share from the
        # collection's shares ref collection
        if self.contents:
            SharedItem(self.contents).shares.remove(self)
        if self.conduit is not None:
            self.conduit.delete(True)
        if self.format is not None:
            self.format.delete(True)
        self.delete(True)

    def put(self, activity=None):
        super(OneTimeShare, self).put(activity=activity)
        collection = self.contents
        self.remove()
        return collection

    def get(self, activity=None):
        super(OneTimeShare, self).get(activity=activity)
        collection = self.contents
        self.remove()
        return collection




class OneTimeFileSystemShare(OneTimeShare):

    formatClass = schema.One(schema.Class)
    translatorClass = schema.One(schema.Class)
    serializerClass = schema.One(schema.Class)
    filePath = schema.One(schema.Text)
    fileName = schema.One(schema.Text)

    def put(self, activity=None):
        self._prepare()
        return super(OneTimeFileSystemShare, self).put(activity=activity)

    def get(self, activity=None):
        self._prepare()
        return super(OneTimeFileSystemShare, self).get(activity=activity)

    def _prepare(self):
        import filesystem_conduit

        if hasattr(self, 'formatClass'):
            self.conduit = filesystem_conduit.FileSystemConduit(
                itsView=self.itsView, sharePath=self.filePath,
                shareName=self.fileName
            )
            self.format = self.formatClass(itsView=self.itsView)
        else:
            self.conduit = \
                filesystem_conduit.FileSystemMonolithicRecordSetConduit(
                itsView=self.itsView,
                sharePath=self.filePath,
                shareName=self.fileName,
                translator=self.translatorClass,
                serializer=self.serializerClass)

