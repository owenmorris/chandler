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
        davETag = dav.etag
        # set serverChanges based on if the etags match
        serverChanges = (etag != davETag)

        # I need to understand the difference between strong etags
        # and weak ones...  for now, pretend they are the same!
        if serverChanges:
            serverChanges = (etag != str('W/' + davETag))
    else:
        # this is the first time this item has been shared.
        needsPut = True
        localChanges = True
        serverChanges = False

    print 'Syncing %s'          % (unicode(dav.url))
    print '-- needsPut      %s' % (needsPut)
    print '-- localChanges  %s' % (localChanges)
    print '-- serverChanges %s' % (serverChanges)
    if serverChanges:
        print '   |-- our etag  %s' % (etag)
        print '   `-- svr etag  %s' % (dav.etag)

    if needsPut:
        dav.putResource(item.itsKind.itsName, 'text/plain')
        item.etag = dav.etag

    if serverChanges:
        # pull down server changes
        davItem = DAVItem.DAVItem(dav)

        # merge any local changes with server changes
        merge(dav, item, davItem, localChanges)


    if localChanges:
        # put back merged local changes
        syncToServer(dav, item)

    if serverChanges or localChanges:
        # Make sure we have the latest etag and lastModified
        # Note: some servers *cough*xythos*cough* change the etag when you
        # do a PROPPATCH
        item.etag = dav.etag
        item.lastModified = dav.lastModified
        item.sharedVersion = item._version





def merge(dav, item, davItem, hasLocalChanges):
    # for now, just pull changes from the server and overwrite local changes...
    print 'Doing merge'
    item.etag = davItem.etag
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
        # don't export these local attributes
        if name in [u'etag', u'lastModified', u'sharedVersion', u'sharedURL']:
            continue

        # the attribute's namespace is its path...
        namespace = kind.getAttribute(name).itsPath[0:-1]

        atype = item.getAttributeAspect(name, 'type')
        acard = item.getAttributeAspect(name, 'cardinality')

        if acard == 'list':
            listData = ''
            for i in value:
                if isinstance(i, Item):
                    defaultURL = dav.url.join(i.itsUUID.str16())
                    durl = i.getAttributeValue('sharedURL', default=defaultURL)
                    # mmm, recursion
                    DAV(durl).put(i)
                    listData += '<itemref>' + unicode(durl) + '</itemref>'
                else:
                    #XXX fix this (Value is a PersistentList here??)
                    #listData += '<value>' + value + '</value>'
                    pass
            props += makePropString(name, namespace, listData)

        elif acard == 'single':
            if isinstance(value, Item):
                defaultURL = dav.url.join(i.itsUUID.str16())
                durl = i.getAttributeValue('sharedURL', default=defaultURL)
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

    #
    # XXX refactor this code with the code above
    #
    if item.isItemOf(Globals.repository.findPath('//parcels/osaf/contentmodel/ItemCollection')):
        listData = ''
        for i in item:
            # mmm, recursion
            defaultURL = dav.url.join(i.itsUUID.str16())
            durl = i.getAttributeValue('sharedURL', default=defaultURL)
            DAV(durl).put(i)
            listData += '<itemref>' + unicode(durl) + '</itemref>'
        props += makePropString('results', '//special/case', listData)
    #
    # End refactor
    #

    r = dav.newConnection().setprops2(url, props)
    #print url, r.status, r.reason
    #print r.read()




def nodesFromXml(data):
    """
    Given a chunk of text that is a flat xml tree like:
      '<foo/><foo/><foo/>'
    parse it and return a list of the nodes
    """
    xmlgoop = davlib.XML_DOC_HEADER + \
              '<doc>' + data + '</doc>'
    doc = libxml2.parseDoc(xmlgoop)
    nodes = doc.xpathEval('/doc/*')
    return nodes


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

            nodes = nodesFromXml(value)

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
            if attr.cardinality == 'list':
                nodes = nodesFromXml(value)
                for node in nodes:
                    item.addValue(name, node.content)
                    print 'Got.....: ', value
            elif attr.cardinality == 'single':
                print 'Got.....: ', value
                item.setAttributeValue(name, attr.type.makeValue(value))


    #
    # XXX refactor this code
    #
    if item.isItemOf(Globals.repository.findPath('//parcels/osaf/contentmodel/ItemCollection')):
        value = davItem._getAttribute('results', '//special/case')

        nodes = nodesFromXml(value)

        serverCollectionResults = []
        for node in nodes:
            otherItem = DAV(node.content).get()
            serverCollectionResults.append(otherItem)

        print 'Merging itemCollection'
        # for now, just sync with whatever the server gave us
        for i in serverCollectionResults:
            if i not in item:
                item.add(i)
        for i in item:
            if i not in serverCollectionResults:
                item.remove(i)
    #
    # End refactor
    #

    item.etag = davItem.etag
    item.lastModified = davItem.lastModified
    item.sharedVersion = item._version # XXX should we commit first?




def getItem(dav):
    repository = Globals.repository

    # Fetch the headers (uuid, kind, etag, lastmodified) from the WebDAV server.
    davItem = DAVItem.DAVItem(dav, True)

    sharing = repository.findPath('//parcels/osaf/framework/GlobalShare') 

    # get the exported item's UUID and see if we have already fetched it
    origUUID = davItem.itsUUID
    try:
        newItem = repository.findUUID(sharing.itemMap[origUUID])
    except:
        newItem = None

    if not newItem:
        # create a new item for the davItem
        kind = davItem.itsKind
        newItem = kind.newItem(None, repository.findPath('//userdata/contentitems'))
        newItem.sharedURL = dav.url
        # set the version to avoid sync thinking there are local changes
        newItem.sharedVersion = newItem._version
        # set a bogus etag so it doesn't try to put
        newItem.etag = "bad-etag"

        # toss this in to the itemMap so we can find it later
        sharing.itemMap[origUUID] = newItem.itsUUID

    dav.sync(newItem)

    return newItem
