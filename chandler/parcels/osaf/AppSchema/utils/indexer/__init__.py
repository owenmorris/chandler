__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from repository.util.Path import Path

def getIndex(name):
    repository = Globals.repository
    ITEM_KIND_PATH = '//Schema/Core/Item'
    INDEX_KIND_PATH = '//Parcels/OSAF/AppSchema/utils/indexer/Index'

    index = repository.find('//userdata/indexes/' + name)
    if index:
        return index

    itemKind = repository.find(ITEM_KIND_PATH)

    userdataItem = repository.find('//userdata')
    if not userdataItem:
        parent = itemKind.newItem('userdata', repository)
        parent = itemKind.newItem('indexes', parent)
    else:
        indexesItem = repository.find('//userdata/indexes')
        if indexesItem:
            parent = indexesItem
        else:
            parent = itemKind.newItem('indexes', userdataItem)

    indexerKind = repository.find(INDEX_KIND_PATH)
    return indexerKind.newItem(name, parent)
