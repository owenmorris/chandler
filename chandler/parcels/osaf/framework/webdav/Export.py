import davlib
import httplib
import xml.sax.saxutils
import libxml2

import application.Globals as Globals
from repository.item.Item import Item

def parseResponse(response):
    """ figure out what the HTTP status was in a multistatus response """
    doc = libxml2.parseDoc(response)

    ctxt = doc.xpathNewContext()
    ctxt.xpathRegisterNs('D', 'DAV:')
    xp = '/D:multistatus/D:response/D:propstat/D:status'
    try:
        node = ctxt.xpathEval(xp)[0]
    except IndexError:
        return None

    return node.content

def putItem(dav, item):
    from Dav import DAV

    # hack to avoid infinite recursion
    # instead of this, we should figure out a way to know if the item has changed since its last
    # etag.. maybe watch for commits?  if it has, then we should see if the thing on the server
    # has changed.. if-match? and then try again.  we gotta get rid of this hack....
    if hasattr(item, 'davified'):
        return
    item.davified = True

    url = unicode(dav.url)

    # need to put an If-Match header here with the item's etag if it exists
    extraHeaders = {}

    etag = item.getAttributeValue('etag', default=None)
    if etag:
        extraHeaders['If-Match'] = etag
    r = dav.newConnection().put(url, item.itsKind.itsName, 'text/plain', None, extraHeaders)

    # now we need to see if this request failed due to the etags being different
    
    # need to handle merging/conflicts here...

    # set them here, even though we have to set them again later
    item.etag = r.getheader('ETag', default='')
    item.lastModified = r.getheader('Last-Modified', default='')

    # ew...
    sharing = Globals.repository.findPath('//parcels/osaf/framework/GlobalShare') 
    sharing.itemMap[item.itsUUID] = item.itsUUID # add an entry here to say that we're already here

    kind = item.itsKind

    propstring = '<osaf:kind xmlns:osaf="//core">%s</osaf:kind><osaf:uuid xmlns:osaf="//core">%s</osaf:uuid>' % (kind.itsPath, item.itsUUID.str16())
    r = dav.newConnection().setprops2(url, propstring)
    print url, r.status, r.reason
    print r.read()

    for (name, value) in item.iterAttributeValues():
        data = ''

        # the attribute's namespace is its path...
        namespace = kind.getAttribute(name).itsPath[0:-1]

        atype = item.getAttributeAspect(name, 'type')
        acard = item.getAttributeAspect(name, 'cardinality')
        if acard == 'list':
            # mmm, recursion
            data = '<osaf:%s xmlns:osaf="%s"><![CDATA[' % (name, namespace)
            for i in value:
                if isinstance(i, Item):
                    durl = dav.url.join(i.itsUUID.str16())
                    DAV(durl).put(i)

                    data = data + '<itemref>' + unicode(durl) + '</itemref>'
                else:
                    # add literal list stuff here
                    pass
            data = data + ']]></osaf:%s>' % (name)
        else:
            if isinstance(value, Item):
                durl = dav.url.join(i.itsUUID.str16())
                DAV(durl).put(i)

                data = '<osaf:%s xmlns:osaf="%s"><![CDATA[<itemref>%s</itemref>]]></osaf:%s>' % (name, namespace, unicode(durl), name)
            else:
                atypepath = "%s" % (atype.itsPath)
                value = atype.makeString(value)
                data = '<osaf:%s xmlns:osaf="%s"><![CDATA[%s]]></osaf:%s>' % (name, namespace, value, name)

        propstring = propstring + data
        #print name, r.status, r.reason
        #r = dc().setprops2(url, str)
        #xmlgoop = r.read()
        #if self.parseResponse(xmlgoop) != 'HTTP/1.1 200 OK':
        #    print url, r.status, r.reason
        #    print str
        #    print xmlgoop

    r = dav.newConnection().setprops2(url, propstring)
    print url, r.status, r.reason
    print r.read()

    # argh!! i hate this.. we have to get the etag again here since
    # some servers *cough*xythos*cough* change the etag when you proppatch
    r = dav.newConnection().head(url)
    item.etag = r.getheader('ETag', default='')
    item.lastModified = r.getheader('Last-Modified', default='')

    return url
    #print propstring
