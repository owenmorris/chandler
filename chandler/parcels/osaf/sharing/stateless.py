#   Copyright (c) 2004-2007 Open Source Applications Foundation
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
    'importFile',
    'exportFile',
]

import logging
import os.path
from osaf import pim
import eim, translator, ics, errors
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

def importFile(rv, path, collection=None, activity=None,
    translatorClass=translator.SharingTranslator,
    serializerClass=ics.ICSSerializer,
    filters=None, debug=False):

    input = open(path, "r")
    text = input.read()
    input.close()

    if filters is None:
        filter = lambda rs: rs
    else:
        filter = eim.Filter(None, u'Temporary filter')
        for uri in filters:
            filter += eim.lookupSchemaURI(uri)
        filter = filter.sync_filter

    trans = translatorClass(rv)

    if activity:
        activity.update(msg=_(u"Parsing file"), totalWork=None)
    inbound, extra = serializerClass.deserialize(text, helperView=rv)

    total = len(inbound)
    if activity:
        activity.update(totalWork=total)

    trans.startImport()
    for alias, rs in inbound.items():
        trans.importRecords(filter(rs))
        if activity:
            activity.update(work=1, msg=_(u"Importing items"))

    trans.finishImport()

    

    if collection is None:
        name = extra.get('name', _(u"Untitled"))
        collection = pim.SmartCollection(itsView=rv, displayName=name)

    for alias in inbound:
        uuid = trans.getUUIDForAlias(alias)
        if uuid:
            item = rv.findUUID(uuid)
            if item is not None:
                collection.add(item)
                pim.setTriageStatus(item, 'auto')
                item_to_change = getattr(item, 'inheritFrom', item)
                item_to_change.read = True

    if activity:
        activity.update(totalWork=None, msg=_(u"Importing complete"))

    return collection


def exportFile(rv, path, collection, activity=None,
    translatorClass=translator.SharingTranslator,
    serializerClass=ics.ICSSerializer,
    filters=None, debug=False):

    if filters is None:
        filter = lambda rs: rs
    else:
        filter = eim.Filter(None, u'Temporary filter')
        for uri in filters:
            filter += eim.lookupSchemaURI(uri)
        filter = filter.sync_filter

    trans = translatorClass(rv)
    trans.startImport()

    total = len(collection)
    if activity:
        activity.update(totalWork=total)

    outbound = { }
    for item in collection:
        if (isinstance(item, pim.Note) and
            pim.EventStamp(item).isTriageOnlyModification()):
            continue # skip triage-only modifications
        
        alias = trans.getAliasForItem(item)
        outbound[alias] = filter(eim.RecordSet(trans.exportItem(item)))
        if activity:
            activity.update(work=1, msg=_(u"Exporting items"))

    text = serializerClass.serialize(outbound, name=collection.displayName,
        monolithic=True)

    output = open(path, "wb")
    output.write(text)
    output.close()

    if activity:
        activity.update(totalWork=None, msg=_(u"Exporting complete"))
