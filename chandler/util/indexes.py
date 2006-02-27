def valueLookup(collection, indexName, attrName, value, multiple=False):

    view = collection.itsView

    def _compare(uuid):
        # Use the new method for getting an attribute value without
        # actually loading an item:
        attrValue = view.findValue(uuid, attrName)
        return cmp(str(value), str(attrValue))

    firstUUID = collection.findInIndex(indexName, 'first', _compare)

    if firstUUID is None: # We're done
        if multiple:
            return []
        else:
            return None

    if multiple: # Let's see if there are more than one
        lastUUID = collection.findInIndex(indexName, 'last', _compare)
        results = []
        for uuid in collection.iterindexkeys(indexName, firstUUID, lastUUID):
            results.append(view[uuid])
        return results

    else:
        return view[firstUUID]


