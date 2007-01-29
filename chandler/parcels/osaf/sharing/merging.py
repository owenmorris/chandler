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

import errors, eim, shares
import logging
from application import schema

logger = logging.getLogger(__name__)


__all__ = [
    'merge',
    'getFilter',
]




def merge(baseline, rsNewBase, inboundDiffs={}, send=True, receive=True,
    filter=None, debug=False):
    """Update states, return send/apply/pending dicts

    rsNewBase is a dict from itemUUID -> recordset for items changed
    since last send, *and* for any items appearing in inboundDiffs (even
    if the item has not been locally changed).  It must always be supplied.

    inboundDiffs is a dict from itemUUID -> the inbound diff recordset.
    It can be omitted if `receive` is false.
    """
    toApply = {}
    toSend  = {}
    pending = {}

    def _filter(rs):
        if filter is None:
            return rs
        else:
            return filter.sync_filter(rs)

    def _cleanDiff(state, diff):
        new_state = state + diff
        new_state.exclusions = set()
        diff = new_state - state
        return diff


    for uuid in set(rsNewBase) | set(inboundDiffs):
        agreed, old_pending = shares.getState(baseline, uuid)
        if debug:
            print " ----------- Merging item:", uuid
            print "   rsNewBase:", rsNewBase.get(uuid, "Nothing")
            print "   inboundDiff:", inboundDiffs.get(uuid, "Nothing")
            print "   agreed:", agreed
            print "   old_pending:", old_pending

        my_state = _filter(rsNewBase.get(uuid, agreed))

        filteredInbound = _filter(inboundDiffs.get(uuid, eim.RecordSet()))
        their_state = agreed + old_pending + filteredInbound

        ncd = (my_state - agreed) | (their_state - agreed)

        if debug:
            print "   my_state:", my_state
            print "   their_state:", their_state
            print "   ncd:", ncd

        dSend = _cleanDiff(their_state, ncd)
        if dSend:
            toSend[uuid] = dSend

        dApply = _cleanDiff(my_state, ncd)
        if dApply:
            toApply[uuid] = dApply

        if send:
            their_state += dSend

        agreed += ncd

        new_pending = their_state - agreed
        if new_pending:
            pending[uuid] = new_pending

        shares.saveState(baseline, uuid, agreed, new_pending)

        if debug:
            print " - - - - Results - - - - "
            print "   agreed:", agreed
            print "   new_pending:", new_pending
            print "   toSend:", toSend
            print "   toApply:", toApply
            print "   pending:", pending
            print " ----------- End of merge "

    return toSend, toApply, pending

def getFilter(filterUris):
    filter = eim.Filter(None, u'Temporary filter')
    for uri in filterUris:
        filter += eim.lookupSchemaURI(uri)
    return filter

