import davlib
import libxml2

from repository.item.Item import Item
from repository.schema.Kind import Kind

import application.Globals

import Dav
import DAVItem

import logging
log = logging.getLogger('sharing')
log.setLevel(logging.DEBUG)

indent = 0

def INC_OFFSET():
    global indent
    indent += 1
    return indent
def DEC_OFFSET():
    global indent
    indent -= 1
    return indent
def OFFSET():
    global indent
    return ' ' * indent


class HistoryChecker(object):
    """
    Used to see if an item has 'really' changed (where sharing is concerned)
    since the last time it was synced.
    """
    def __init__(self, item):
        self.item = item
        self.dirty = False

    def isDirty(self):
        if not self.dirty:
            sharedVersion = self.item.sharedVersion
            if sharedVersion == 0:
                sharedVersion = 1
            self.item.itsView.mapHistory(self._histfunc,
                                         sharedVersion,
                                         0)
        return self.dirty

    def _histfunc(self, item, version, status, values, references):
        if self.dirty:
            return
        if self.item == item:
            log.info('%s|- Checking dirty...' % (OFFSET()))
            log.info('%s|  |- values: %s' % (OFFSET(), values))
            log.info('%s|  `- refs:   %s' % (OFFSET(), references))
            for value in values:
                if value not in [u'etag', u'sharedURL', u'sharedVersion']:
                    self.dirty = True
                    return

            for reference in references:
                if reference not in [u'itemCollectionResults']:
                    self.dirty = True
                    return


def syncItem(dav, item):
    # changes flags
    needsPut = False
    localChanges = False
    serverChanges = False

    offset = OFFSET()
    log.info('%sSyncing %s (%s)' % (offset, unicode(dav.url), item.getItemDisplayName()))

    # see if the local version has changed by comparing the last shared version
    # with the item's current version
    if item.sharedVersion != item._version:
        if item.sharedVersion == -1:
            localChanges = True
        else:
            localChanges = HistoryChecker(item).isDirty()

    try:
        # fetch the server item here. so we don't have to do it below for serverChanges.
        # we should really send along an If-Modified header
        davItem = DAVItem.DAVItem(dav)
        davETag = davItem.etag
        etag = item.getAttributeValue('etag', default=None)

        # set serverChanges based on if the etags match
        serverChanges = (etag != davETag)

        # I need to understand the difference between strong etags
        # and weak ones...  for now, pretend they are the same!
        if serverChanges:
            serverChanges = (etag != str('W/' + davETag))
    except Dav.NotFound:
        # this is the first time this item has been shared.
        needsPut = True
        localChanges = True
        serverChanges = False

    log.info('%s|- needsPut      %s' % (offset, needsPut))
    log.info('%s|- localChanges  %s' % (offset, localChanges))
    log.info('%s|  `- versions   %s : %s' % (offset, item.sharedVersion, item._version))
    log.info('%s`- serverChanges %s' % (offset, serverChanges))
    if serverChanges:
        log.info('%s   |-- our etag  %s' % (offset, etag))
        log.info('%s   `-- svr etag  %s' % (offset, davETag))

    if needsPut:
        dav.putResource(item.itsKind.itsName, 'text/plain')
        item.etag = dav.etag

    if serverChanges:
        # Use the davItem we fetched earlier
        # merge any local changes with server changes
        merge(dav, item, davItem, localChanges)

        del davItem

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
    item.etag = davItem.etag
    syncFromServer(item, davItem)


def mergeList(item, attrName, nodes, nodesAreItemRefs):
    list = item.getAttributeValue(attrName, default=[])

    serverList = []
    for node in nodes:
        if nodesAreItemRefs:
            INC_OFFSET()
            try:
                value = Dav.DAV(node.content).get()
            except Dav.NotFound:
                value = None
            DEC_OFFSET()
        else:
            value = node.content

        if value:
            serverList.append(value)

    log.info('%sMerging List: %s in %s' % (OFFSET(), attrName, str(item)))
    try:
        # for now, just sync with whatever the server gave us
        for i in serverList:
            if i not in list:
                item.addValue(attrName, i)
                log.info('%sAdding %s to list %s' % (OFFSET(), i, item))
        # XXX this should work but has some issues.. fixme!
        #for i in list:
        #    if i not in serverList:
        #        item.removeValue(attrName, i)
        #        log.info('%sremoving %s from list %s' % (OFFSET(), i, item))

    except Exception, e:
        log.exception(e)
            


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
                    u'sharedURL', u'sharedUUID', u'collectionOwner',
                    u'itemCollectionResults',
                    u'itemCollectionInclusions',
                    u'itemCollectionInclusions'
                    u'itemCollectionExclusions']:
            continue

        # XXX this is probably not the best thing to do here
        # but for now, if an attribute starts with a '_', don't share it
        if name[0] == u'_':
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
    if item.isItemOf(item.itsView.findPath('//parcels/osaf/contentmodel/ItemCollection')):
        listData = ''
        for i in item:
            # mmm, recursion
            try:
                durl = i.sharedURL
            except AttributeError:
                durl = dav.url.join(i.itsUUID.str16())

            # in theory, this should be done by the cloud, but the results
            # aren't showing up in the cloud...
            #DAV(durl).put(i)
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
    kind = davItem.itsKind

    # we need to make sure that the kind of the item is the same as the one on
    # the server
    if item.itsKind != kind:
        log.info('%sKind changed from %s to %s' % (OFFSET(), str(item.itsKind), kind))
        item.itsKind = kind

    for (name, attr) in kind.iterAttributes(True):

        value = davItem.getAttribute(attr)
        if not value:
            continue

        log.info('%sGetting: %s (%s)' % (OFFSET(), name, attr.type.itsName))

        # see if its an ItemRef or not
        if isinstance(attr.type, Kind):
            # time for some xml parsing! yum!

            nodes = nodesFromXml(value)
            if len(nodes) == 0:
                continue

            if attr.cardinality == 'list':
                # replaced by mergeList + continue
                #setfunc = item.addValue
                mergeList(item, name, nodes, True)
                continue
            elif attr.cardinality == 'single':
                node = nodes[0]
                INC_OFFSET()
                try:
                    otherItem = Dav.DAV(node.content).get()
                    item.setAttributeValue(name, otherItem)
                except Dav.NotFound:
                    log.warning('Cant access %s' % (node.content))
                DEC_OFFSET()
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
                log.info('%sGot.....: %s' % (OFFSET(), value))
                item.setAttributeValue(name, attr.type.makeValue(value))


    #
    # XXX refactor this code
    #
    if item.isItemOf(item.itsView.findPath('//parcels/osaf/contentmodel/ItemCollection')):
        value = davItem._getAttribute('results', '//special/case')

        nodes = nodesFromXml(value)

        serverCollectionResults = []
        for node in nodes:
            INC_OFFSET()
            otherItem = Dav.DAV(node.content).get()
            DEC_OFFSET()
            serverCollectionResults.append(otherItem)

        log.debug('Merging itemCollection')
        # for now, just sync with whatever the server gave us
        for i in serverCollectionResults:
            if i not in item:
                item.add(i)
                log.debug('adding %s to collection %s' % (i, item))

        # XXX this should work but has some issues.. fixme!
        #        for i in item:
        #            if i not in serverCollectionResults:
        #                item.remove(i)
        #                log.debug('removing %s from collection %s' % (i, item))

    #
    # End refactor
    #

    item.etag = davItem.etag
    #item.lastModified = davItem.lastModified
    item.sharedVersion = item._version # XXX should we commit first?




def getItem(dav):
    repository = application.Globals.repository

    # Fetch the headers (uuid, kind, etag, lastmodified) from the WebDAV server.
    davItem = DAVItem.DAVItem(dav, True)

    sharing = repository.findPath('//parcels/osaf/framework/GlobalShare')

    # get the exported item's UUID and see if we have already fetched it
    origUUID = davItem.itsUUID
    try:
        newItem = repository.findUUID(sharing.itemMap[origUUID])
        log.info('%sUpdating existing item %s' % (OFFSET(), newItem))
    except: # XXX figure out if this is a KeyError or an AttributeError
        newItem = None
        log.info('%sExisting item not found for %s' % (OFFSET(), unicode(dav.url)))

    if not newItem:
        # create a new item for the davItem
        kind = davItem.itsKind
        newItem = kind.newItem(None, repository.findPath('//userdata/contentitems'))
        newItem.sharedURL = dav.url
        newItem.sharedUUID = origUUID
        # set the version to avoid sync thinking there are local changes
        newItem.sharedVersion = newItem._version

        # toss this in to the itemMap so we can find it later
        sharing.itemMap[origUUID] = newItem.itsUUID


    # since we may already have local items, we need to walk the collection
    # and sync up the clouds of the items in the collection.  If we don't do this
    # we may look at the collection and think it hasn't changed when in reality
    # one of its items may have changed....
    # Should changing any item in a collection's cloud poke the collection when it
    # is changed?  If we did that, I think we could remove most of this code...
    if newItem.isItemOf(repository.findPath('//parcels/osaf/contentmodel/ItemCollection')):
        contentItemKind = repository.findPath('//parcels/osaf/contentmodel/ContentItem')
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
