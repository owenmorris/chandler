
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from libxml2 import createPushParser

from repository.remote.ItemFilter import ItemFilter
from chandlerdb.util.UUID import UUID
from repository.util.SAX import ContentHandler, XMLOffFilter
from repository.persistence.RepositoryError import NoSuchItemError


class CloudFilter(ItemFilter):

    def __init__(self, cloud, store, uuid, version, generator):

        ItemFilter.__init__(self, store, uuid, version, generator)
        self.cloud = cloud
        self.endpoints = {}

    def parse(self, xml, uuids):

        ItemFilter.parse(self, xml)

        for uuid, endpoints in self.endpoints.iteritems():
            if not uuid in uuids:
                doc = self.store.loadItem(self.version, uuid)
                if doc is None:
                    raise NoSuchItemError, (uuid, self.version)
                xml = doc.getContent()

            for endpoint in endpoints:
                endpoint.writeItems(1, uuid, self.version,
                                    self.generator, xml, uuids)
        
    def kindEnd(self, attrs):

        assert attrs['type'] == 'uuid'
        kind = self.repository.find(UUID(self.data))

        if self.cloud is None:
            clouds = kind.getClouds()
            if clouds:
                self.cloud = clouds.first()
        elif not kind.isKindOf(self.cloud.kind):
            raise TypeError, '%s is not a kind this cloud (%s) understands' %(kind.itsPath, self.cloud.itsPath)

    def refEnd(self, attrs):

        uuid = UUID(self.data)
        name = attrs['name']
        generator = self.generator

        if self.cloud is not None:
            endpoints = self.cloud.getAttributeEndpoints(name)
        else:
            endpoints = None

        def processRef(ref):
            output = True
            if endpoints:
                for endpoint in endpoints:
                    policy = endpoint.includePolicy
                    length = len(endpoint.attribute)
                    if length == 1 and policy == 'none':
                        output = False
                    elif length > 1 or policy != 'byRef':
                        eps = self.endpoints.get(ref[0], None)
                        if eps is not None:
                            eps.append(endpoint)
                        else:
                            self.endpoints[ref[0]] = [ endpoint ]
            return output

        if 'first' in attrs:
            first = True
            alias = {}
            for ref in self.store.loadRefs(self.version, self.uuid, uuid,
                                           UUID(attrs['first'])):
                if processRef(ref):
                    if first:
                        first = False
                        attrs['uuid'] = self.data
                        generator.startElement('ref', attrs)

                    if ref[4] is not None:
                        alias['alias'] = ref[4]
                        generator.startElement('ref', alias)
                    else:
                        generator.startElement('ref', None)
                        
                    generator.characters(ref[0].str64())
                    generator.endElement('ref')
            if not first:
                generator.endElement('ref')
                    
        elif processRef((uuid, uuid, None, None, None)):
            generator.startElement('ref', attrs)
            generator.characters(self.data)
            generator.endElement('ref')


class EndpointFilter(ItemFilter):

    def __init__(self, endpoint, store, uuid, version, generator):

        ItemFilter.__init__(self, store, uuid, version, generator)
        self.endpoint = endpoint

    def refEnd(self, attrs):

        uuid = UUID(self.data)
        name = attrs['name']
        generator = self.generator

        if 'first' in attrs:
            first = True
            alias = {}
            for ref in self.store.loadRefs(self.version, self.uuid, uuid,
                                           UUID(attrs['first'])):
                if first:
                    first = False
                    attrs['uuid'] = self.data
                    generator.startElement('ref', attrs)

                if ref[4] is not None:
                    alias['alias'] = ref[4]
                    generator.startElement('ref', alias)
                else:
                    generator.startElement('ref', None)

                generator.characters(ref[0].str64())
                generator.endElement('ref')
            if not first:
                generator.endElement('ref')
                    
        else:
            generator.startElement('ref', attrs)
            generator.characters(self.data)
            generator.endElement('ref')


class RefHandler(ContentHandler):

    def __init__(self, endpoint, name, uuid, version):

        ContentHandler.__init__(self)

        self.repository = endpoint.itsView
        self.name = name
        self.uuid = uuid
        self.version = version
        self.values = None

        self.data = ''
        self._attrs = []

    def parse(self, xml):

        createPushParser(self, xml, len(xml), 'handler').parseChunk('', 0, 1)
        if self.errorOccurred():
            raise self.saxError()
        
    def startElement(self, tag, attrs):

        if not self.errorOccurred():
            self.data = ''
            self._attrs.append(attrs)

    def characters(self, data):

        self.data += data

    def endElement(self, tag):

        if not self.errorOccurred():
            attrs = self._attrs.pop()
            if tag == 'ref':
                try:
                    self.refEnd(attrs)
                except Exception:
                    self.saveException()

    def refEnd(self, attrs):

        if attrs['name'] == self.name:
            uuid = UUID(self.data)

            if 'first' in attrs:
                store = self.repository.repository.store
                first = UUID(attrs['first'])
                self.values = [ ref[0] for ref in store.loadRefs(self.version,
                                                                 self.uuid,
                                                                 uuid, first) ]
            else:
                self.values = [ uuid ]
