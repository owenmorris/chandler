__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from repository.util.Path import Path

__all__ = ['getIndex']

def getIndex(name):
    repository = Globals.repository
    ITEM_KIND_PATH = '//Schema/Core/Item'
    INDEX_KIND_PATH = '//parcels/OSAF/framework/utils/indexer/Index'

    index = repository.find('//userdata/indexes/' + name)
    if index:
        return index

    indexerKind = repository.find(INDEX_KIND_PATH)
    return indexerKind.newItem(name, __getParent())

def __getParent():
    """ get or create //userdata/indexes """
    repository = Globals.repository

    parent = repository.find('//userdata/indexes')
    if parent:
        return parent

    itemKind = repository.find('//Schema/Core/Item')
    userdata = repository.find('//userdata')
    if not userdata:
        userdata = itemKind.newItem('userdata', repository)

    return itemKind.newItem('indexes', userdata)
