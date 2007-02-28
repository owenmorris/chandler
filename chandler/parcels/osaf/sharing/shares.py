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
__all__ = [
    'Share',
    'OneTimeShare',
    'OneTimeFileSystemShare',
    'SharedItem',
    'State',
    'Conflict',
    'getFilter',
    'isShared',
    'isReadOnly',
]


from application import schema
from osaf import pim
from i18n import ChandlerMessageFactory as _
import errors, eim, translator, model
from eim import NoChange as nc
from callbacks import *
import cPickle
import logging
import datetime
from PyICU import ICUtzinfo

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

    conflictingStates = schema.Sequence()

    def getConflicts(self):
        for state in getattr(self, 'conflictingStates', []):
            for conflict in state.getConflicts():
                yield conflict


    def clearConflicts(self):
        for state in getattr(self, 'conflictingStates', []):
            state.clearConflicts()


    def generateConflicts(self, **kwds):
        # TODO: replace this with something that generates more interesting
        # conflicts
        if not hasattr(self, 'conflictingStates'):
            itemUUID = self.itsItem.itsUUID.str16()
            peer = pim.EmailAddress(itsView=self.itsItem.itsView,
                emailAddress="conflict@example.com")
            state = State(itsView=self.itsItem.itsView, peer=peer,
                itemUUID=itemUUID)

            state.pending = eim.RecordSet([
                model.ItemRecord(itemUUID, "XYZZY", nc, nc, nc, nc),
                model.NoteRecord(itemUUID, "PLUGH", nc, nc),
                model.EventRecord(itemUUID, nc, nc, "San Jose", nc, nc, nc,
                    nc, nc),
            ])
            state.updateConflicts()


    def addPeerState(self, state, peer):
        peerUuid = peer.itsUUID.str16()
        if not hasattr(self, 'peerStates'):
            self.peerStates = []
        if state not in self.peerStates:
            self.peerStates.append(state, peerUuid)
        state.itemUUID = self.itsItem.itsUUID.str16()

    def getPeerState(self, peer, create=True):
        peerUuid = peer.itsUUID.str16()
        state = None
        if hasattr(self, 'peerStates'):
            state = self.peerStates.getByAlias(peerUuid)
        else:
            self.peerStates = []
        if state is None and create:
            state = State(itsView=self.itsItem.itsView, peer=peer,
                itemUUID=self.itsItem.itsUUID.str16())
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
        me = schema.ns("osaf.pim", self.itsItem.itsView).currentContact.item
        basedAttributeNames = None # we'll look these up if necessary
        isSharedInAnyReadOnlyShares = False
        for share in self.sharedIn:
            if getattr(share, 'sharer', None) is not me:   # inbound share
                if share.mode in ('put', 'both'):   # writable share
                    return True
                else:                               # read-only share
                    # We found a read-only share; this attribute isn't
                    # modifiable if it's one of the attributes shared for
                    # this item in this share. (First, map this attribute to
                    # the 'real' attributes it depends on, if we haven't yet.)
                    if basedAttributeNames is None:
                        basedAttributeNames = self.itsItem.getBasedAttributes(attribute)
                    for attr in basedAttributeNames:
                        # @@@MOR: Should this be self.itsKind or self.itsItem.itsKind?
                        if attr in share.getSharedAttributes(self.itsItem.itsKind):
                            isSharedInAnyReadOnlyShares = True

        return not isSharedInAnyReadOnlyShares






class State(schema.Item):

    peer = schema.One(schema.ItemRef)
    peerStateFor = schema.One(inverse=SharedItem.peerStates)
    peerRepoId = schema.One(schema.Text, initialValue="")
    peerItemVersion = schema.One(schema.Integer, initialValue=-1)
    itemUUID = schema.One(schema.Text)
    conflictFor = schema.One(inverse=SharedItem.conflictingStates)

    # Internal
    _agreed = schema.One(schema.Text)
    _pending = schema.One(schema.Text)

    # TODO: add translator here?

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
        send=True, receive=True, filter=None, debug=False):

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
        externalDiff = rsExternal - self.agreed

        if debug:
            print " ----------- Merging item:", self.itemUUID
            print "   rsInternal:", rsInternal
            print "   isDiff:", isDiff
            print "   inbound:", inbound
            print "   externalDiff:", externalDiff
            print "   agreed:", self.agreed
            print "   pending:", pending

        ncd = internalDiff | filter(externalDiff)
        self.agreed += (internalDiff | externalDiff)

        if debug:
            print "   rsExternal:", rsExternal
            print "   ncd:", ncd

        dSend = self._cleanDiff(rsExternal, ncd)

        dApply = self._cleanDiff(rsInternal, ncd)

        if send:
            rsExternal += dSend


        self.pending = rsExternal - self.agreed

        # Hook up pending conflicts to item
        self.updateConflicts()

        if debug:
            print " - - - - Results - - - - "
            print "   agreed:", self.agreed
            print "   dSend:", dSend
            print "   dApply:", dApply
            print "   pending:", self.pending
            print " ----------- End of merge "

        return dSend, dApply, self.pending

    def _cleanDiff(self, state, diff):
        newState = state + diff
        newState.exclusions = set()
        diff = newState - state
        return diff

    def updateConflicts(self):
        # See if we have pending conflicts; if so, make sure we are in the
        # item's conflictingStates ref collection.  If not, make sure we
        # aren't.  Also, if we're the last conflict to be removed from the
        # item, go ahead and delete the conflictingStates attribute.
        if hasattr(self, "itemUUID"):
            uuid = self.itemUUID
            item = self.itsView.findUUID(uuid)
            if item is not None:
                if not pim.has_stamp(item, SharedItem):
                    SharedItem(item).add()
                shared = SharedItem(item)
                if self.pending:
                    if not hasattr(shared, 'conflictingStates'):
                        shared.conflictingStates = []
                    shared.conflictingStates.add(self)
                else:
                    if self in getattr(shared, 'conflictingStates', []):
                        shared.conflictingStates.remove(self)
                        if not shared.conflictingStates:
                            del shared.conflictingStates


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
        self.getTranslator().importRecords(change)
        self.agreed += change
        self.discard(change)

    def discard(self, change):
        pending = self.pending
        pending.remove(change)
        self.pending = pending
        self.agreed += change
        self.updateConflicts()

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
        return translator.PIMTranslator(self.itsView)







class Conflict(object):

    resolved = False

    def __init__(self, state, field, value, change):
        self.state = state
        self.peer = state.peer
        self.field = field
        self.value = value
        self.change = change

    def __repr__(self):
        return "%s : %s" % (self.field, self.value)

    def apply(self):
        if not self.resolved:
            self.state.apply(self.change)
            self.resolved = True

    def discard(self):
        if not self.resolved:
            self.state.discard(self.change)
            self.resolved = True





def getFilter(filterUris):
    filter = eim.Filter(None, u'Temporary filter')
    for uri in filterUris:
        filter += eim.lookupSchemaURI(uri)
    return filter





def isShared(item):
    return pim.has_stamp(item, SharedItem)

def isReadOnly(item):
    """
    Examine all the shares this item participates in; if any of those
    shares are writable the item is not readonly.  If all the shares
    are read-only the item is readonly.
    """
    if not isShared(item):
        return False

    sharedItem = SharedItem(item)
    if hasattr(sharedItem, 'sharedIn'):
        for share in self.sharedIn:
            if share.mode in ('put', 'both'):
                return False
    return True




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
        doc = 'A message describing the last error; empty string otherwise',
        initialValue = u''
    )

    lastSynced = schema.One(schema.DateTimeTZ)

    contents = schema.One(inverse=SharedItem.shares, initialValue=None)
    items = schema.Sequence(inverse=SharedItem.sharedIn, initialValue=[])

    conduit = schema.One(initialValue=None)
    # inverse of Conduit.share

    format = schema.One(initialValue=None)
    # inverse of ImportExportFormat.share

    states = schema.Sequence(State, inverse=schema.One(), initialValue=[])

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

    def __init__(self, *args, **kw):
        defaultDisplayName = getattr(kw.get('contents'),'displayName',u'')
        kw.setdefault('displayName',defaultDisplayName)

        # Stamp contents as a SharedItem if not already
        if 'contents' in kw:
            contents = kw['contents']
            if contents is not None and not pim.has_stamp(contents, SharedItem):
                SharedItem(contents).add()

        super(Share, self).__init__(*args, **kw)

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


    def create(self):
        self.conduit.create()

    def destroy(self):
        self.conduit.destroy()

    def open(self):
        self.conduit.open()

    def close(self):
        self.conduit.close()

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None,
        debug=False):
        stats = self.conduit.sync(modeOverride=modeOverride,
                                  updateCallback=updateCallback,
                                  forceUpdate=forceUpdate, debug=debug)
        self.lastSynced = datetime.datetime.now(ICUtzinfo.default)
        return stats

    def put(self, updateCallback=None):
        return self.sync(modeOverride='put', updateCallback=updateCallback,
                         forceUpdate=None)

    def get(self, updateCallback=None):
        return self.sync(modeOverride='get', updateCallback=updateCallback)

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







class OneTimeShare(Share):
    """
    Delete format, conduit, and share after the first get or put.
    """

    def remove(self):
        # With deferred deletes, we need to also remove the Share from the
        # collection's shares ref collection
        if self.contents:
            SharedItem(self.contents).shares.remove(self)
        self.conduit.delete(True)
        self.format.delete(True)
        self.delete(True)

    def put(self, updateCallback=None):
        super(OneTimeShare, self).put(updateCallback=updateCallback)
        collection = self.contents
        self.remove()
        return collection

    def get(self, updateCallback=None):
        super(OneTimeShare, self).get(updateCallback=updateCallback)
        collection = self.contents
        self.remove()
        return collection




class OneTimeFileSystemShare(OneTimeShare):
    def __init__(self, path, itsName, formatclass, itsKind=None, itsView=None,
                 contents=None):

        import filesystem_conduit
        conduit = filesystem_conduit.FileSystemConduit(
            itsKind=itsKind, itsView=itsView, sharePath=path, shareName=itsName
        )
        format  = formatclass(itsView=itsView)
        super(OneTimeFileSystemShare, self).__init__(
            itsKind=itsKind, itsView=itsView,
            contents=contents, conduit=conduit, format=format
        )

