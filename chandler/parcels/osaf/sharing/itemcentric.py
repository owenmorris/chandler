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
import eim, eimml, translator, shares, errors
from i18n import ChandlerMessageFactory as _
import logging

logger = logging.getLogger(__name__)


__all__ = [
    'inbound',
    'outbound',
    'outboundDeletion',
    'getPeerState',
]


# Item-centric peer-to-peer sharing

def inbound(peer, text, allowDeletion=False, debug=False):

    rv = peer.itsView

    # At some point, which serializer and translator to use should be
    # configurable
    serializer = eimml.EIMMLSerializer # only using class methods
    trans = translator.PIMTranslator(rv)

    inbound, extra = serializer.deserialize(text)

    # Only one recordset is allowed
    if len(inbound) != 1:
        raise errors.MalformedData(_("Only one recordset allowed"))

    peerRepoId = extra.get('repo', None)
    peerItemVersion = int(extra.get('version', '-1'))

    uuid, rsExternal = inbound.items()[0]

    item = rv.findUUID(uuid)

    if rsExternal is not None:

        if item is not None: # Item already exists
            if not pim.has_stamp(item, shares.SharedItem):
                shares.SharedItem(item).add()
            shared = shares.SharedItem(item)
            state = getPeerState(shared, peer)
            rsInternal= eim.RecordSet(trans.exportItem(item))

        else: # Item doesn't exist yet
            state = shares.State(itsView=rv, peer=peer)
            rsInternal = eim.RecordSet()

        if peerRepoId != state.peerRepoId:
            # This update is not from the peer repository we last saw.
            # Treat the update is entirely new
            state.clear()
            state.peerRepoId = peerRepoId

        # Only process recordsets whose version is greater than the last one
        # we say.  In the case of null-repository-view testing, versions are
        # always stuck at zero, so process those as well.

        if (peerItemVersion == 0) or (peerItemVersion > state.peerItemVersion):
            state.peerItemVersion = peerItemVersion

            dSend, dApply, pending = state.merge(rsInternal, rsExternal,
                send=False, receive=True, uuid=uuid, debug=debug)

            if dApply:
                if debug: print "Applying:", uuid, dApply
                trans.importRecords(dApply)

            item = rv.findUUID(uuid)
            if item is not None and item.isLive():
                if not pim.has_stamp(item, shares.SharedItem):
                    shares.SharedItem(item).add()
                shared = shares.SharedItem(item)
                if not hasattr(shared, 'states'):
                    shared.states = []
                if state not in shared.states:
                    shared.states.append(state, peer.itsUUID.str16())
        else:
            logger.info("Ignoring old update for %s", uuid)

    else: # Deletion

        # Remove the state
        if pim.has_stamp(item, shares.SharedItem):
            shared = shares.SharedItem(item)
            if hasattr(shared, 'states'):
                state = shared.states.getByAlias(peer.itsUUID.str16())
                if state is not None:
                    shared.states.remove(state)
                    state.delete(True)

        # Remove the item (if allowed)
        if allowDeletion:
            if debug: print "Deleting item:", uuid
            item.delete(True)
            item = None

    return item



def outbound(peer, item, debug=False):

    rv = peer.itsView

    # At some point, which serializer and translator to use should be
    # configurable
    serializer = eimml.EIMMLSerializer # only using class methods
    trans = translator.PIMTranslator(rv)

    uuid = item.itsUUID.str16()
    rsInternal = eim.RecordSet(trans.exportItem(item))

    if not pim.has_stamp(item, shares.SharedItem):
        shares.SharedItem(item).add()

    shared = shares.SharedItem(item)

    # Abort if pending
    if shared.getConflicts():
        raise errors.ConflictsPending(_(u"Conflicts pending"))

    state = getPeerState(shared, peer)

    # Set agreed state to what we have locally
    state.agreed = rsInternal

    # Repository identifier:
    if rv.repository is not None:
        repoId = rv.repository.getSchemaInfo()[0].str16()
    else:
        repoId = ""

    text = serializer.serialize({uuid : rsInternal}, "item", repo=repoId,
        version=str(item.itsVersion))

    return text




def outboundDeletion(peer, uuid, debug=False):

    rv = peer.itsView

    # At some point, which serializer and translator to use should be
    # configurable
    serializer = eimml.EIMMLSerializer # only using class methods

    return serializer.serialize({ uuid : None }, "item")



def getPeerState(item, peer, create=True):

    peerUuid = peer.itsUUID.str16()
    state = None
    if hasattr(item, 'states'):
        state = item.states.getByAlias(peerUuid)
    else:
        item.states = []
    if state is None and create:
        state = shares.State(itsView=item.itsItem.itsView, peer=peer)
        item.states.append(state, peerUuid)
    return state

