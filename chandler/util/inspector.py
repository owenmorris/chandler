
def iterItemHistory(view, uuid, fromVersion=1, toVersion=0):

    store = view.store
    prevValues = set()

    if fromVersion > 1:

        for version, status in store.iterItemVersions(None, uuid,
            fromVersion - 1, 0, True):

            then, viewSize, commitCount, name = store.getCommit(version)
            reader, uValues = store.loadValues(None, version, uuid)
            prevValues = set(uValues)
            break

    for version, status in store.iterItemVersions(None, uuid,
        fromVersion, toVersion):

        then, viewSize, commitCount, name = store.getCommit(version)
        reader, uValues = store.loadValues(None, version, uuid)
        currValues = set(uValues)
        # removed values not included
        names = [store.loadItemName(None, version, uAttr)
                 for uAttr in (reader.readAttribute(None, uValue)
                               for uValue in currValues - prevValues)]

        values = []
        for name in names:
            values.append((name, view.findValue(uuid, name, version=version)))

        yield version, values
        prevValues = currValues


def printItemHistory(view, uuid, fromVersion=1, toVersion=0):
    for version, values in iterItemHistory(view, uuid, fromVersion=fromVersion,
        toVersion=toVersion):
        print version
        for name, value in values:
            print "%s: %s" % (name, value)
