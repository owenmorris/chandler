import davlib
import libxml2

import application.Globals as Globals
from repository.item.Item import Item
from repository.schema.Kind import Kind

import DAVItem as DAVItem


def syncItem(dav, item):
    # changes flags
    needsPut = False
    localChanges = False
    serverChanges = False

    # see if the local version has changed by comparing the last shared version
    # with the item's current version
    if item.sharedVersion != item._version:
        localChanges = True

    etag = item.getAttributeValue('etag', default=None)
    if etag:
        # set serverChanges based on if the etags match
        serverChanges = (etag != dav.etag)
    else:
        # this is the first time this item has been shared.
        needsPut = True
        localChanges = True
        serverChanges = False

    print 'Syncing %s'          % (unicode(dav.url))
    print '-- needsPut      %s' % (needsPut)
    print '-- localChanges  %s' % (localChanges)
    print '-- serverChanges %s' % (serverChanges)

    if needsPut:
        dav.putResource(item.itsKind.itsName, 'text/plain')
        item.etag = dav.etag

    if serverChanges:
        # pull down server changes
        davItem = DAVItem.DAVItem(dav)

        # merge any local changes with server changes
        try:
            merge(dav, item, davItem, localChanges)
        except:
            pass

    if localChanges:
        # put back merged local changes
        syncToServer(dav, item)




def merge(dav, item, davItem, hasLocalChanges):
    # for now, just pull changes from the server and overwrite local changes...
    print 'Doing merge'
    syncFromServer(item, davItem)




def makePropString(name, namespace, value):
    header = '<o:%s xmlns:o="%s"><![CDATA[' % (name, namespace)
    footer = ']]></o:%s>' % (name)
    return header + unicode(value) + footer

def syncToServer(dav, item):
    from Dav import DAV
    url = unicode(dav.url)

    # set them here, even though we have to set them again later
    item.sharedVersion = item._version

    kind = item.itsKind

    # build a giant property string and then do a PROPPATCH
    props = makePropString('kind', '//core', kind.itsPath) + \
            makePropString('uuid', '//core', item.itsUUID.str16())

    for (name, value) in item.iterAttributeValues():
        # the attribute's namespace is its path...
        namespace = kind.getAttribute(name).itsPath[0:-1]

        atype = item.getAttributeAspect(name, 'type')
        acard = item.getAttributeAspect(name, 'cardinality')

        if acard == 'list':
            listData = ''
            for i in value:
                if isinstance(i, Item):
                    # mmm, recursion
                    durl = dav.url.join(i.itsUUID.str16())
                    DAV(durl).put(i)
                    listData += '<itemref>' + unicode(durl) + '</itemref>'
                else:
                    # XXX TODO add literal list stuff here
                    pass
            props += makePropString(name, namespace, listData)

        elif acard == 'single':
            if isinstance(value, Item):
                durl = dav.url.join(value.itsUUID.str16())
                DAV(durl).put(value)
                props += makePropString(name, namespace, '<itemref>%s</itemref>' % (unicode(durl)))
            else:
                atypepath = "%s" % (atype.itsPath)
                props += makePropString(name, namespace, atype.makeString(value))

        elif acard == 'dict':
            # XXX implement me
            pass
        else:
            raise Exception

    r = dav.newConnection().setprops2(url, props)
    print url, r.status, r.reason
    print r.read()

    # argh!! i hate this.. we have to get the etag again here since
    # some servers *cough*xythos*cough* change the etag when you proppatch
    item.etag = dav.etag
    item.lastModified = dav.lastModified
    item.sharedVersion = item._version




def syncFromServer(item, davItem):
    from Dav import DAV
    kind = davItem.itsKind

    for (name, attr) in kind.iterAttributes(True):

        value = davItem.getAttribute(attr)
        if not value:
            continue

        print 'Getting:', name, '(' + attr.type.itsName + ')'

        # see if its an ItemRef or not
        if isinstance(attr.type, Kind):
            # time for some xml parsing! yum!

            # given a chunk of text that is a flat xml tree like:
            # "<foo/><foo/><foo/>"
            # parse it and return a list of the nodes
            xmlgoop = davlib.XML_DOC_HEADER + \
                      '<doc>' + value + '</doc>'
            doc = libxml2.parseDoc(xmlgoop)
            nodes = doc.xpathEval('/doc/*')

            if attr.cardinality == 'list':
                setfunc = item.addValue
            elif attr.cardinality == 'single':
                setfunc = item.setAttributeValue
            elif attr.cardinality == 'dict':
                # XXX implement me
                pass
            else:
                raise Exception
            for node in nodes:
                otherItem = DAV(node.content).get()
                setfunc(name, otherItem)

        else:
            print 'Got.....: ', value
            item.setAttributeValue(name, attr.type.makeValue(value))

    item.etag = davItem.etag
    item.lastModified = davItem.lastModified
    item.sharedVersion = item._version # XXX should we commit first?




def getItem(dav):
    repository = Globals.repository

    # fetch the item
    davItem = DAVItem.DAVItem(dav)

    sharing = repository.findPath('//parcels/osaf/framework/GlobalShare') 

    # get the exported item's UUID and see if we have already fetched it
    origUUID = davItem.itsUUID
    newItem = repository.findUUID(sharing.itemMap[origUUID])
    if newItem:
        syncItem(dav, newItem)
        return newItem

    # otherwise, create a new item for the davItem
    kind = davItem.itsKind
    newItem = kind.newItem(None, repository.findPath('//userdata/contentitems'))

    # XXX i'd much rather just call syncItem() here... 
    syncFromServer(newItem, davItem)

    return newItem
