import application.Globals as Globals

import davlib
import httplib
import libxml2

itemMap = {}

class BadItem(Exception):
    pass

class DAVItem(object):
    """ utility class that represents an item from a webdav server """
    def __init__(self, dav):
        super(DAVItem, self).__init__()

        self.dav = dav

        self.doc = self._allprop(unicode(dav.url))

    def _allprop(self, url, depth = 0):
        """ Fetch all the properties of a resource """
        body = davlib.XML_DOC_HEADER + \
               '<D:propfind xmlns:D="DAV:">' + \
               '<D:allprop/>' + \
               '</D:propfind>'

        r = self.dav.newConnection().propfind(url, body, depth)

        xmlgoop = r.read()
        print url
        print xmlgoop

        doc = libxml2.parseDoc(xmlgoop)

        return doc

    def getKind(self):
        value = self._getAttribute('kind', '//core')
        if not value:
            raise BadItem, 'Unable to find a kind at %s' % (self.dav.url)

        return Globals.repository.findPath(value)

    def getUUID(self):
        value = self._getAttribute('uuid', '//core')
        if not value:
            raise BadItem, 'Unable to find a uuid at %s' % (self.dav.url)

        from repository.util.UUID import UUID
        return UUID(value)

    def getAttribute(self, attr):
        """ takes an Attribute argument """
        attrname = attr.itsName
        
        attrns = str(attr.itsPath[0:-1])
        return self._getAttribute(attrname, attrns)

    def _getAttribute(self, attr, attrns):
        ctxt = self.doc.xpathNewContext()
        ctxt.xpathRegisterNs('D', 'DAV:')
        ctxt.xpathRegisterNs('O', attrns)

        xp = '/D:multistatus/D:response/D:propstat/D:prop/O:' + attr
        try:
            node = ctxt.xpathEval(xp)[0]
        except IndexError:
            return None

        # Do I need to free the context?
        return node.content


def makeAndParse(xml):
    xmlgoop = davlib.XML_DOC_HEADER + \
              '<doc>' + \
              xml + \
              '</doc>'

    doc = libxml2.parseDoc(xmlgoop)
    nodes = doc.xpathEval('/doc/*')
    return nodes


def getItem(dav):
    from Dav import DAV
    from repository.util.URL import URL
    global itemMap
    repository = Globals.repository

    # fetch the item
    di = DAVItem(dav)

    # pretend here we don't care if the item has changed..
    try:
        # get the exported item's UUID and see if we have already fetched it
        oldUUID = di.getUUID()
        return repository.findUUID(itemMap[oldUUID])
    except KeyError:
        pass

    # ugh
    kindType = type(repository.findPath('//Schema/Core/Kind'))

    kind = di.getKind()
    newItem = kind.newItem(None, repository.findPath('//userdata/zaobaoitems'))

    # XXX hack...
    itemMap[oldUUID] = newItem.itsUUID.str16()

    for (name, attr) in kind.iterAttributes(True):

        value = di.getAttribute(attr)
        if not value:
            continue

        print 'Getting:', name, '(' + attr.type.itsName + ')'

        if type(attr.type) == kindType:
            if len(value) < 5: # skip things that are shorter than <a/>
                continue

            # time for some xml parsing! yum!
            nodes = makeAndParse(value)

            if attr.cardinality == 'list':
                for node in nodes:
                    otherItem = DAV(URL(node.content)).get()
                    newItem.addValue(name, otherItem)
            elif attr.cardinality == 'single':
                node = nodes[0]
                otherItem = findOtherItem(node.content)
                newItem.setAttributeValue(name, otherItem)
            else:
                raise Exception

        else:
            #newItem.setAttributeValue(name, value)
            print 'Got.....: ', value
            newItem.setAttributeValue(name, attr.type.makeValue(value))

    return newItem
