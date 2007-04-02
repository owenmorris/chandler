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
import eim, shares
import logging

logger = logging.getLogger(__name__)


__all__ = [
    'serialize',
    'deserialize',
]



def serialize(rv, items, translator, serializer, filter=None, debug=False):

    if filter is None:
        filter = lambda rs: rs
    else:
        filter = filter.sync_filter

    trans = translator(rv)

    rsInternal = { }

    for item in items:
        alias = trans.getAliasForItem(item)
        rsInternal[alias] = filter(eim.RecordSet(trans.exportItem(item)))

        if not pim.has_stamp(item, shares.SharedItem):
            shares.SharedItem(item).add()

        shared = shares.SharedItem(item)

    text = serializer.serialize(rsInternal)

    return text





def deserialize(rv, peer, text, translator, serializer, filter=None,
    debug=False):

    items = []

    trans = translator(rv)

    inbound, extra = serializer.deserialize(text)

    for alias, rsExternal in inbound.items():

        uuid = trans.getUUIDForAlias(alias)
        if uuid:
            item = rv.findUUID(uuid)
        else:
            item = None

        if rsExternal is not None:

            if item is not None: # Item already exists
                if not pim.has_stamp(item, shares.SharedItem):
                    shares.SharedItem(item).add()
                shared = shares.SharedItem(item)
                state = shared.getPeerState(peer)
                rsInternal= eim.RecordSet(trans.exportItem(item))

            else: # Item doesn't exist yet
                state = shares.State(itsView=rv, peer=peer)
                rsInternal = eim.RecordSet()

            dSend, dApply, pending = state.merge(rsInternal, rsExternal,
                isDiff=False, filter=filter, debug=debug)

            state.updateConflicts(item)

            if dApply:
                if debug: print "Applying:", uuid, dApply
                trans.startImport()
                trans.importRecords(dApply)
                trans.finishImport()

            uuid = trans.getUUIDForAlias(alias)
            if uuid:
                item = rv.findUUID(uuid)
            else:
                item = None

            if item is not None and item.isLive():
                if not pim.has_stamp(item, shares.SharedItem):
                    shares.SharedItem(item).add()
                shares.SharedItem(item).addPeerState(state, peer)

                items.append(item)

    return items
