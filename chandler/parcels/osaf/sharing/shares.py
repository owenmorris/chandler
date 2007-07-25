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
from chandlerdb.util.c import Empty
from repository.item.Item import Item

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
        return getConflicts(self.itsItem)



    def generateConflicts(self, **kwds):
        # TODO: replace this with something that generates more interesting
        # conflicts
        if not self.conflictingStates:
            itemUUID = self.itsItem.itsUUID.str16()
            peer = pim.EmailAddress.getEmailAddress(self.itsItem.itsView,
                                                    "conflict@example.com")
            state = State(itsView=self.itsItem.itsView, peer=peer)

            state.pending = eim.Diff([
                model.ItemRecord(itemUUID, "An alterative title", nc, nc, nc, nc, nc),
                model.NoteRecord(itemUUID, "A different note", nc, nc, nc, nc),
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

        # XXX This isn't true for preview...
        # slow path -- item is shared; we need to look at all the *inbound*
        # shares this item participates in -- if *any* of those inbound shares
        # are writable, the attribute is modifiable; otherwise, if *all* of
        # those inbound shares are read-only, but none of those shares
        # actually *share* that attribute (i.e., it's being filtered either
        # by sharing cloud or explicit filter), then it's modifiable.
        
        # For preview, make all attributes unmodifiable if any shares it
        # participates in are read-only
        import utility
        return not utility.isReadOnly(self.itsItem)

        #for share in self.sharedIn:
            #if share.isAttributeModifiable(self.itsItem, attribute):
                #return True

        #return False
        
    @schema.observer(conflictingStates)
    def onConflictingStatesChange(self, op, name):
        # CommunicationStatus might have changed
        self.itsItem.updateDisplayWho(op, name)



def hasConflicts(item):
    item = getattr(item, 'proxiedItem', item)
    return len(getattr(item, SharedItem.conflictingStates.name, [])) > 0


def getConflicts(item):
    item = getattr(item, 'proxiedItem', item)
    # conflicts = []
    for state in getattr(item, SharedItem.conflictingStates.name, []):
        for conflict in state.getConflicts():
            conflict.item = item
            yield conflict
            # conflicts.append(conflict)

    if item.hasLocalAttributeValue(SharedItem.conflictingStates.name):
        # the conflicts we just looked at where not inherited, but if
        # we are a modification our master might also have conflicts
        if pim.has_stamp(item, pim.EventStamp):
            event = pim.EventStamp(item)
            master = event.getMaster()
            if master is not event:
                for conflict in getConflicts(master.itsItem):
                    yield conflict




class State(schema.Item):

    peer = schema.One(schema.ItemRef)
    peerStateFor = schema.One(inverse=SharedItem.peerStates)
    peerRepoId = schema.One(schema.Text, initialValue="")
    peerItemVersion = schema.One(schema.Integer, initialValue=-1)
    conflictFor = schema.One(inverse=SharedItem.conflictingStates)
    share = schema.One()
    conflictingShare = schema.One()
    pendingRemoval = schema.One(schema.Boolean, initialValue=False)

    # Internal
    _agreed = schema.One(schema.Bytes)
    _pending = schema.One(schema.Bytes)


    def __repr__(self):
        return "State(%r, %r)" % (self.agreed, self.pending)


    def getAgreed(self):
        if hasattr(self, '_agreed'):
            return eim.RecordSet(cPickle.loads(self._agreed))
        else:
            return eim.RecordSet()

    def setAgreed(self, agreed):
        assert isinstance(agreed, eim.RecordSet)
        self._agreed = cPickle.dumps(agreed.inclusions)

    def delAgreed(self):
        del self._agreed

    agreed = property(getAgreed, setAgreed, delAgreed)



    def getPending(self):
        if hasattr(self, '_pending'):
            return eim.Diff(*cPickle.loads(self._pending))
        else:
            return eim.Diff()

    def setPending(self, pending):
        assert isinstance(pending, eim.Diff)
        self._pending = cPickle.dumps((pending.inclusions, pending.exclusions))

    def delPending(self):
        del self._pending

    pending = property(getPending, setPending, delPending)



    def merge(self, rsInternal, inbound=None, isDiff=True,
        filter=None, readOnly=False, debug=False):
        assert isinstance(rsInternal, eim.RecordSet)

        if filter is None:
            filter = lambda rs: rs
        else:
            filter = filter.sync_filter

        pending = self.pending
        agreed  = self.agreed

        # We need to set rsExternal to equal the entire external state

        # If we're passing in a diff, apply it to agreed + pending
        if isDiff:
            rsExternal = agreed + pending + (inbound or eim.Diff())
        elif isinstance(inbound, eim.Diff):
            rsExternal = eim.RecordSet() + inbound
        else:
            rsExternal = inbound or eim.RecordSet()
        assert isinstance(rsInternal, eim.RecordSet)

        internalDiff = filter(rsInternal - agreed)
        externalDiff = filter(rsExternal - agreed)
        ncd = internalDiff | externalDiff

        msgs = list()
        add = msgs.append
        add("----------- Beginning merge")
        add("   old agreed: %s" % agreed)
        add("   old pending: %s" % pending)
        add("   rsInternal: %s" % rsInternal)
        add("   internalDiff: %s" % internalDiff)
        add("   rsExternal: %s" % rsExternal)
        add("   externalDiff: %s" % externalDiff)
        add("   ncd: %s" % ncd)

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

            extWins = agreed + internalDiff + pending + externalDiff
            intWins = agreed + pending + externalDiff + internalDiff
            add("   extWins: %s" % extWins)
            add("   intWins: %s" % intWins)
            pending = self.pending = filter(extWins - intWins)

            agreed = self.agreed = filter(rsExternal)
            dSend = eim.Diff()

        else:
            agreed = self.agreed = agreed + ncd
            # add("   agreed+=ncd: %s" % agreed)
            dSend = self._cleanDiff(rsExternal, ncd)
            # add("   dSend cleanDiff: %s" % dSend)
            rsExternal += dSend
            # add("   rsExternal+=dSend: %s" % rsExternal)
            pending = self.pending = filter(rsExternal - agreed)

        dApply = self._cleanDiff(rsInternal, ncd)


        add(" - - - - Results - - - - ")
        add("   dSend: %s" % dSend)
        add("   dApply: %s" % dApply)
        add("   new agreed: %s" % agreed)
        add("   new pending: %s" % pending)
        add(" ----------- Merge complete")

        if pending:
            msgs.insert(0, "Conflict detected:")

        doLog = logger.info if (debug or pending) else logger.debug
        for msg in msgs:
            doLog(msg)

        return dSend, dApply, pending

    def _cleanDiff(self, state, diff):
        assert isinstance(state, eim.RecordSet)        
        return (state + diff) - state

    def updateConflicts(self, item):
        # See if we have pending conflicts; if so, make sure we are in the
        # item's conflictingStates ref collection.  If not, make sure we
        # aren't.
        if item is not None:
            if not pim.has_stamp(item, SharedItem):
                SharedItem(item).add()
            shared = SharedItem(item)
            if self.pendingRemoval or self.pending:
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
        self.pendingRemoval = False

    def apply(self, change):
        translator = self.getTranslator()
        logger.info("Applying pending conflicts")
        for rec in change.inclusions:
            logger.info("<< ++ %s", rec)
        for rec in change.exclusions:
            logger.info("<< -- %s", rec)
        translator.startImport()
        translator.importRecords(change)
        translator.finishImport()
        self.agreed += change
        self.discard(change)

    def discard(self, change):
        try:
            pending = self.pending
            pending.remove(change)
            self.pending = pending
        except KeyError:
            # the pending change has already been removed
            pass
        self.agreed += change

    def getConflicts(self):
        if self.pendingRemoval:
            yield Conflict(self, None, None, None, pendingRemoval=True)

        elif self.pending:
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




    def autoResolve(self, rsInternal, dApply, dSend):
        trans = self.getTranslator()
        for rConflict, field in self._iterConflicts():
            logger.info("Examining conflict for EIM auto-resolution")
            rLocal = findMatch(rConflict, rsInternal)
            rAgreed = findMatch(rConflict, self.agreed)
            logger.info("Local: %s", rLocal)
            logger.info("Remote: %s", rConflict)
            logger.info("Agreed: %s", rAgreed)

            if rLocal: # rLocal will be None if the conflict is 
                       # a record deletion, which this auto-resolve
                       # code doesn't yet support

                if rAgreed in (eim.NoChange, eim.Inherit):
                    agreedValue = rAgreed
                else:
                    agreedValue = (field.__get__(rAgreed) if rAgreed
                                   else eim.NoChange)

                localValue = field.__get__(rLocal)
                remoteValue = field.__get__(rConflict)

                decision = trans.resolve(type(rConflict), field,
                    agreedValue, localValue, remoteValue)

                if decision == -1: # local wins
                    dLocal = eim.Diff([rLocal])
                    dSend += dLocal
                    self.agreed += dLocal

                elif decision == 1: # remote wins
                    dConflict = eim.Diff([rConflict])
                    dApply += dConflict
                    self.agreed += dConflict

                if decision:
                    newPending = self.pending
                    newPending.remove(rConflict)
                    self.pending = newPending
                    logger.info("Resolved; state updated to: %s", self)
                else:
                    logger.info("Not resolved")


    def _iterConflicts(self):
        # Break a pending Diff into records, each containing one conflicting
        # field.  This results in records that could be applied if you want the
        # pending change to win in a conflict.
        for r in self.pending.inclusions:
            cls = type(r)
            data = [(f.__get__(r) if isinstance(f, eim.key) else eim.NoChange)
                for f in cls.__fields__]
            for f, value in zip(cls.__fields__, r[1:]):
                if not isinstance(f, eim.key) and value is not eim.NoChange:
                    data[f.offset-1] = value
                    yield cls(*data), f
                    data[f.offset-1] = eim.NoChange


def findMatch(record, recordSet):
    # Given a record as returned from iterConflicts, find the record with the
    # same key within recordSet and return a copy of that record, but only
    # the fields that were not NoChange in the first arg record will be filled
    # in in the copy (while the rest will be NoChange).  This results in a
    # record that could be applied if you choose the local value to win in a
    # conflict.
    cls = type(record)
    key = record.getKey()

    for r in recordSet.inclusions:
        if key == r.getKey():
            data = [(f.__get__(r) if f.__get__(record) is not eim.NoChange
                else eim.NoChange) for f in cls.__fields__]
            return cls(*data)

    return None




class Conflict(object):

    resolved = False

    def __init__(self, state, field, value, change, pendingRemoval=False):
        self.state = state
        self.peer = getattr(state, 'peer', None)
        self.field = field
        self.value = value
        self.change = change
        self.item = None
        self.pendingRemoval = pendingRemoval

    def __repr__(self):
        return "%s : %s" % (self.field, self.value)


    def apply(self):

        if not self.resolved:

            if self.pendingRemoval:
                peer = self.state.peer
                if peer and isinstance(peer, Share) and self.item is not None:
                    # remove the item from the collection it's shared in
                    if self.item in peer.contents:
                        peer.contents.remove(self.item)

                self.state.conflictFor = None
                self.state.conflictingShare = None
                self.state.delete(True)

            else:
                self.state.apply(self.change)
                if self.item is not None:
                    self.state.updateConflicts(self.item)
            self.resolved = True



    def discard(self):
        if not self.resolved:
            if self.pendingRemoval:
                self.state.pendingRemoval = False
            else:
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
        sharedItem = SharedItem(item)
        if not pim.has_stamp(item, SharedItem):
            logger.info("Stamping item %s as SharedItem", item.itsUUID)
            sharedItem.add()
        if item not in self.items:
            logger.info("Adding item %s to sharedIn", item.itsUUID)
            self.items.add(item)


    def removeSharedItem(self, item):
        """ Remove an item from the share's sharedIn refcoll, unstamping if
            the last share for this item """
        if not pim.has_stamp(item, SharedItem):
            return
        sharedItem = SharedItem(item)
        logger.info("Removing item %s from sharedIn", item.itsUUID)
        self.items.remove(item)
        if not sharedItem.sharedIn:
            logger.info("Unstamping item %s as SharedItem", item.itsUUID)
            sharedItem.remove()

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

        self.lastAttempt = datetime.datetime.now(self.itsView.tzinfo.default)

        # Clear any previous error
        for linked in self.getLinkedShares():
            if hasattr(linked, 'error'):
                del linked.error
            if hasattr(linked, 'errorDetails'):
                del linked.errorDetails

        try:
            # If someone else has modified a collection in the middle of our
            # sync we'll get a TokenMismatch.  Try again a couple more times...
            tries = 3
            while True:
                try:
                    stats = self.conduit.sync(modeOverride=modeOverride,
                        activity=activity, forceUpdate=forceUpdate,
                        debug=debug)
                    break
                except errors.TokenMismatch:
                    tries -= 1
                    if tries == 0:
                        raise

            # Not sure we need to keep the last stats around.  It's just more
            # data to persist.  If it ends up being helpful we can put it back
            # in:

            # self.lastStats = stats

            self.lastSuccess = datetime.datetime.now(self.itsView.tzinfo.default)

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

    def reset(self):
        # As a last resort, if the user has encountered a sharing error
        # and needs to get unstuck, delete all the state items from the
        # share and reset the conduit.
        for state in getattr(self, 'states', []):
            self.states.remove(state)
            state.delete(True)

        if self.conduit and hasattr(self.conduit, 'reset'):
            self.conduit.reset()

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






