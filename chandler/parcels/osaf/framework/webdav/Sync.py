import davlib
import libxml2

import application.Globals as Globals
from repository.item.Item import Item
from repository.schema.Kind import Kind

import Dav
import DAVItem as DAVItem

import logging
log = logging.getLogger('sharing')
log.setLevel(logging.INFO)

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

    log.info('Syncing %s (%s)' % (unicode(dav.url), item.getItemDisplayName()))
    log.info('-- needsPut      %s' % (needsPut))
    log.info('-- localChanges  %s' % (localChanges))
    log.info('-- serverChanges %s' % (serverChanges))
    if serverChanges:
        log.info('   |-- our etag  %s' % (etag))
        log.info('   `-- svr etag  %s' % (davETag))

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

        # because some server suck (moddav) and don't change the etag
        # when you change properties, lets force this
        # maybe use a "ptag" property instead of etags so we can change it
        # whenever
        dav.putResource(item.itsKind.itsName, 'text/plain')


    if serverChanges or localChanges:
        # Make sure we have the latest etag and lastModified
        # Note: some servers *cough*xythos*cough* change the etag when you
        # do a PROPPATCH
        item.etag = dav.etag
        #item.lastModified = dav.lastModified
        item.sharedVersion = item._version





def merge(dav, item, davItem, hasLocalChanges):
    # for now, just pull changes from the server and overwrite local changes...
    log.debug('Doing merge')
    item.etag = davItem.etag
    syncFromServer(item, davItem)


def mergeList(item, attrName, nodes, nodesAreItemRefs):
    from Dav import DAV, NotFound
    list = item.getAttributeValue(attrName, default=[])

    serverList = []
    for node in nodes:
        if nodesAreItemRefs:
            try:
                value = DAV(node.content).get()
            except NotFound:
                value = None
        else:
            value = node.content

        if value:
            serverList.append(value)

    log.debug('Merging List: %s in %s' % (attrName, str(item)))
    # for now, just sync with whatever the server gave us
    for i in serverList:
        if i not in list:
            item.addValue(attrName, i)
            log.debug('adding %s to list %s' % (i, item))
    for i in list:
        if i not in serverList:
            item.removeValue(attrName, i)
            log.debug('removing %s from list %s' % (i, item))



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

    # we don't ever want to actually change the UUID value on the server
    # so if we already have one here use it
    uuid = item.getAttributeValue('sharedUUID', default=item.itsUUID)
    props = makePropString('kind', '//core', kind.itsPath) + \
            makePropString('uuid', '//core', uuid)

    for (name, value) in item.iterAttributeValues():
        # don't export these local attributes
        if name in [u'etag', u'lastModified', u'sharedVersion',
                    u'sharedURL', u'sharedUUID']:
            continue

        # the attribute's namespace is its path...
        namespace = kind.getAttribute(name).itsPath[0:-1]

        atype = item.getAttributeAspect(name, 'type')
        acard = item.getAttributeAspect(name, 'cardinality')

        if acard == 'list':
            listData = ''
            for i in value:
                if isinstance(i, Item):
                    try:
                        durl = i.sharedURL
                    except AttributeError:
                        durl = dav.url.join(i.itsUUID.str16())
                    listData += '<itemref>' + unicode(durl) + '</itemref>'
                else:
                    #XXX fix this (Value is a PersistentList here??)
                    #listData += '<value>' + value + '</value>'
                    pass
            props += makePropString(name, namespace, listData)

        elif acard == 'single':
            if isinstance(value, Item):
                try:
                    durl = value.sharedURL
                except AttributeError:
                    durl = dav.url.join(value.itsUUID.str16())
                    log.debug('Cant export %s -- Not a ContentItem' % (str(value)))

                props += makePropString(name, namespace, '<itemref>%s</itemref>' % (unicode(durl)))
                    
            elif atype is not None:
                atypepath = "%s" % (atype.itsPath)
                try:
                    # this will only succeed if the attribute is Text
                    dataString = value.getReader().read()
                except AttributeError:
                    dataString = value
                props += makePropString(name, namespace, dataString)

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

    r = dav.setProps(props)
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
    from Dav import DAV, NotFound
    kind = davItem.itsKind

    for (name, attr) in kind.iterAttributes(True):

        value = davItem.getAttribute(attr)
        if not value:
            continue

        log.info('Getting: %s (%s)' % (name, attr.type.itsName))

        # see if its an ItemRef or not
        if isinstance(attr.type, Kind):
            # time for some xml parsing! yum!

            nodes = nodesFromXml(value)

            if attr.cardinality == 'list':
                # replaced by mergeList + continue
                #setfunc = item.addValue
                mergeList(item, name, nodes, True)
                continue
            elif attr.cardinality == 'single': 
                try:
                    otherItem = DAV(node.content).get()
                    item.setAttributeValue(name, otherItem)
                except NotFound:
                    log.warning('Cant access %s' % (node.content))
            elif attr.cardinality == 'dict':
                # XXX implement me
                log.info('NOTIMPLEMENTED Trying to share cardinality dict attribute' % (node.content))
            else:
                raise Exception

        else:
            if attr.cardinality == 'list':
                nodes = nodesFromXml(value)
                # mergeList replaces this code
                #for node in nodes:
                #    item.addValue(name, node.content)
                #    log.info('Got.....: ', value)
                mergeList(item, name, nodes, False)
            elif attr.cardinality == 'single':
                log.info('Got.....: %s' % (value))
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

        log.debug('Merging itemCollection')
        # for now, just sync with whatever the server gave us
        for i in serverCollectionResults:
            if i not in item:
                item.add(i)
                log.debug('adding %s to collection %s' % (i, item))
        for i in item:
            if i not in serverCollectionResults:
                item.remove(i)
                log.debug('removing %s from collection %s' % (i, item))

    #
    # End refactor
    #

    item.etag = davItem.etag
    #item.lastModified = davItem.lastModified
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
    except: # XXX figure out if this is a KeyError or an AttributeError
        newItem = None

    if not newItem:
        # create a new item for the davItem
        kind = davItem.itsKind
        newItem = kind.newItem(None, repository.findPath('//userdata/contentitems'))
        newItem.sharedURL = dav.url
        newItem.sharedUUID = origUUID
        # set the version to avoid sync thinking there are local changes
        newItem.sharedVersion = newItem._version
        # XXX set a bogus etag so it doesn't try to put
        newItem.etag = "bad-etag"

        # toss this in to the itemMap so we can find it later
        sharing.itemMap[origUUID] = newItem.itsUUID


    if newItem.isItemOf(Globals.repository.findPath('//parcels/osaf/contentmodel/ItemCollection')):
        contentItemKind = Globals.repository.findPath('//parcels/osaf/contentmodel/ContentItem')
        for i in newItem:
            clouds = i.itsKind.getClouds('default')
            for cloud in clouds:
                for k in cloud.getItems(i):
                    # we only support publishing content items
                    
                    if not k.isItemOf(contentItemKind):
                        log.warning('Skipping %s -- Not a ContentItem' % (str(k)))
                        continue
                    if not k.hasAttributeValue('sharedURL'):
                        continue
                    Dav.DAV(k.sharedURL).sync(k)

    dav.sync(newItem)

    return newItem
