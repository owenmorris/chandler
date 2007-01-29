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
    'READWRITE',
    'READONLY',
    'UNSHARED',
    'getSharedState', #hmm, perhaps rename this
    'saveState',
    'getState',
    'removeState',
    'hasState',
    'discardPending',
    'getBaselineUuids',
    'Baseline'
]


from application import schema
from osaf import pim
from i18n import ChandlerMessageFactory as _
import errors, eim
from callbacks import *
import logging

import logging
logger = logging.getLogger(__name__)


READWRITE = 'read-write'
READONLY = 'read-only'
UNSHARED = 'unshared'

class SharedItem(pim.Stamp):
    schema.kindInfo(annotates=pim.ContentItem)

    shares = schema.Sequence(initialValue=[])
    # 'shares' is used to link collection to their shares

    sharedIn = schema.Sequence(initialValue=[])
    # 'sharedIn' links shared items to their shares

    baselines = schema.Sequence(initialValue=[])
    # 'baselines' is used only for p2p sharing, including mail-edit-update.
    # In Cosmo-based sharing, baselines are stored in the conduit's baseline

    def getConflicts(self):
        uuid = self.itsItem.itsUUID.str16()
        conflicts = { }

        for baseline in getattr(self, 'baselines', []):
            if hasState(baseline, uuid):
                agreed, pending = getState(baseline, uuid)
                if pending:
                    conflicts[baseline.peer] = pending

        return conflicts


    def getSharedState(self): # TODO: rename this
        """
        Examine all the shares this item participates in; if any of those
        shares are writable the shared state is READWRITE.  If all the shares
        are read-only the shared state is READONLY.  Otherwise UNSHARED.
        """

        state = UNSHARED
        if hasattr(self, 'sharedIn'):
            for share in self.sharedIn:
                state = READONLY
                if share.mode in ('put', 'both'):
                    return READWRITE
        return state


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

# -----------

USE_PICKLE = True
if USE_PICKLE:
    import cPickle

class Baseline(schema.Item):
    baselineFor = schema.One(inverse=SharedItem.baselines)
    peer = schema.One(schema.Text)

class State(schema.Item):
    deleted = schema.One(schema.Boolean, defaultValue=False)

    if USE_PICKLE:
        agreed = schema.One(schema.Text)
        pending = schema.One(schema.Text)
    else:
        agreed = schema.Sequence(schema.Tuple)
        pending_inclusions = schema.Sequence(schema.Tuple)
        pending_exclusions = schema.Sequence(schema.Tuple)


def saveState(baseline, uuidString, agreed, new_pending):
    if USE_PICKLE:
        State.update(baseline, uuidString,
            deleted=False,
            agreed=cPickle.dumps(agreed),
            pending=cPickle.dumps(new_pending))
    else:
        State.update(baseline, uuidString,
            deleted=False,
            agreed=list(agreed.inclusions),
            pending_inclusions=list(new_pending.inclusions),
            pending_exclusions=list(new_pending.exclusions))




def getState(baseline, uuidString):
    state = baseline.getItemChild(uuidString)

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

def removeState(baseline, uuidString):
    state = baseline.getItemChild(uuidString)
    if state is not None:
        state.deleted = True

def hasState(baseline, uuidString):
    state = baseline.getItemChild(uuidString)
    return state is not None and not state.deleted

def discardPending(baseline, uuidString):
    if hasState(baseline, uuidString):
        agreed, pending = getState(baseline, uuidString)
        saveState(baseline, uuidString, agreed, eim.RecordSet())

def getBaselineUuids(baseline):
    for state in baseline.iterChildren():
        if state.isLive():
            yield state.itsName

# -----------



def getSharedState(item): # TODO: rename this
    if not pim.has_stamp(item, SharedItem):
        return UNSHARED
    else:
        return SharedItem(item).getSharedState()


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

    contents = schema.One(inverse=SharedItem.shares, initialValue=None)
    items = schema.Sequence(inverse=SharedItem.sharedIn, initialValue=[])

    conduit = schema.One(initialValue=None)
    # inverse of Conduit.share

    format = schema.One(initialValue=None)
    # inverse of ImportExportFormat.share

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

    def addSharedItem(self, item, baseline=None):
        if not pim.has_stamp(item, SharedItem):
            SharedItem(item).add()
        sharedItem = SharedItem(item)
        sharedItem.sharedIn = self
        if baseline is not None:
            if not hasattr(sharedItem, 'baselines'):
                sharedItem.baselines = [baseline]
            elif baseline not in sharedItem.baselines:
                sharedItem.baselines.add(baseline)

    def removeSharedItem(self, item, baseline=None):
        if not pim.has_stamp(item, SharedItem):
            return
        sharedItem = SharedItem(item)
        sharedItem.sharedIn.remove(self)
        if (baseline is not None and
            baseline in getattr(sharedItem, 'baselines', [])):
            sharedItem.baselines.remove(baseline)
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
        return self.conduit.sync(modeOverride=modeOverride,
                                 updateCallback=updateCallback,
                                 forceUpdate=forceUpdate, debug=debug)

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

