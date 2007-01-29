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
import eim, eimml, translator, shares, merging
import logging

logger = logging.getLogger(__name__)


__all__ = [
    'inbound',
    'outbound',
    'outboundDeletion',
]


# Item-centric peer-to-peer sharing

def inbound(rv, peer, text, allowDeletion=False, debug=False):

    # At some point, which serializer and translator to use should be
    # configurable
    serializer = eimml.EIMMLSerializer # only using class methods
    trans = translator.PIMTranslator(rv)

    inbound, extra = serializer.deserialize(text)

    # Only one recordset is allowed
    if len(inbound) != 1:
        raise errors.MalformedData(_("Only one recordset allowed"))

    uuid, rs = inbound.items()[0]

    item = rv.findUUID(uuid)

    if rs is not None:

        if item is not None: # Item already exists
            if not pim.has_stamp(item, shares.SharedItem):
                shares.SharedItem(item).add()
            shared = shares.SharedItem(item)
            baseline = getPeerBaseline(shared, peer)
            rsNewBase = {
                uuid : eim.RecordSet(trans.exportItem(item))
            }

        else: # Item doesn't exist yet
            baseline = shares.Baseline(itsView=rv, peer=peer)
            rsNewBase = { uuid : eim.RecordSet() }

        toSend, toApply, pending = merging.merge(baseline, rsNewBase,
            inbound, send=False, receive=True, debug=debug)

        if toApply.has_key(uuid):
            apply = toApply[uuid]
            if debug: print "Applying:", uuid, apply
            trans.importRecords(apply)

        item = rv.findUUID(uuid)
        if item is not None and item.isLive():
            if not pim.has_stamp(item, shares.SharedItem):
                shares.SharedItem(item).add()
            shared = shares.SharedItem(item)
            shared.baselines.add(baseline)

    else: # Deletion
        deletePeerBaseline(item, peer)
        if allowDeletion:
            if debug: print "Deleting item:", uuid
            item.delete(True)
            item = None

    return item



def outbound(rv, peer, item, debug=False):

    # At some point, which serializer and translator to use should be
    # configurable
    serializer = eimml.EIMMLSerializer # only using class methods
    trans = translator.PIMTranslator(rv)

    uuid = item.itsUUID.str16()
    rsNewBase = { uuid : eim.RecordSet(trans.exportItem(item)) }

    if not pim.has_stamp(item, shares.SharedItem):
        shares.SharedItem(item).add()

    shared = shares.SharedItem(item)
    baseline = getPeerBaseline(shared, peer)

    toSend, toApply, pending = merging.merge(baseline, rsNewBase,
        send=True, receive=False, debug=debug)

    if toSend:
        text = serializer.serialize(toSend, "item")
    else:
        text = None

    return text




def outboundDeletion(rv, peer, uuid, debug=False):

    # At some point, which serializer and translator to use should be
    # configurable
    serializer = eimml.EIMMLSerializer # only using class methods

    return serializer.serialize({ uuid : None }, "item")



def getPeerBaseline(item, peer, create=True):
    for baseline in getattr(item, 'baselines', []):
        if baseline.peer == peer:
            return baseline
    if create:
        return shares.Baseline(itsView=item.itsItem.itsView, peer=peer)
    else:
        return None



def deletePeerBaseline(item, peer):
    if pim.has_stamp(item, shares.SharedItem):
        shared = shares.SharedItem(item)
        baseline = getPeerBaseline(shared, peer, create=False)
        if baseline:
            baseline.delete(True)

