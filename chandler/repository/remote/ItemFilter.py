
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.util.UUID import UUID
from repository.util.SAX import XMLOffFilter


class ItemFilter(XMLOffFilter):

    def __init__(self, store, uuid, version, generator):

        XMLOffFilter.__init__(self, generator, 'ref', 'text', 'binary')

        self.store = store
        self.repository = store.repository.view
        self.uuid = uuid
        self.version = version
        self.data = ''
        
        self._attrs = []

    def startElement(self, tag, attrs):

        if not self.errorOccurred():
            self.data = ''
            method = getattr(self, tag + 'Start', None)
            if method is not None:
                try:
                    method(attrs)
                except Exception:
                    self.saveException()
            self._attrs.append(attrs)

        XMLOffFilter.startElement(self, tag, attrs)

    def characters(self, data):

        self.data += data
        XMLOffFilter.characters(self, data)

    def cdataBlock(self, data):

        self.data += data
        XMLOffFilter.cdataBlock(self, data)

    def endElement(self, tag):

        if not self.errorOccurred():
            attrs = self._attrs.pop()
            method = getattr(self, tag + 'End', None)
            if method is not None:
                try:
                    method(attrs)
                except Exception:
                    self.saveException()

        XMLOffFilter.endElement(self, tag)

    def textEnd(self, attrs):

        value = self.repository._getLobType('text')(self.repository)
        value.load(self.data, attrs)
        generator = self.generator
        
        attrs['type'] = 'text'
        attrs['uuid'] = self.data
        generator.startElement('text', attrs)

        reader = value.getReader()
        generator.cdataSection(None, True, False)
        while True:
            data = reader.read(1024)
            if data:
                generator.cdataSection(data, False, False)
            else:
                generator.cdataSection(None, False, True)
                break
        reader.close()

        generator.endElement('text')
