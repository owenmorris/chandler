
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from libxml2mod import xmlEncodeSpecialChars as escape
from libxml2 import SAXCallback


class ContentHandler(SAXCallback):
    
    def cdataBlock(self, data):
        
        self.characters(data)


class XMLGenerator(object):

    def __init__(self, out, encoding='utf-8'):

        self.out = out
        self.encoding = encoding

    def startDocument(self):

        self.out.write('<?xml version="1.0" encoding="%s"?>' %(self.encoding))

    def endDocument(self):

        self.out.flush()

    def startElement(self, tag, attrs):

        self.out.write('<')
        self.out.write(tag)
        if attrs:
            for name, value in attrs.iteritems():
                if isinstance(value, unicode):
                    value = value.encode(self.encoding)
                self.out.write(' ')
                self.out.write(name)
                self.out.write('="')
                self.out.write(escape(None, value))
                self.out.write('"')
                
        self.out.write('>')

    def endElement(self, tag):

        self.out.write('</')
        self.out.write(tag)
        self.out.write('>')
    
    def characters(self, data):

        if isinstance(data, unicode):
            data = data.encode(self.encoding)

        self.out.write(escape(None, data))

    def cdataSection(self, data):

        if isinstance(data, unicode):
            data = data.encode(self.encoding)

        self.out.write('<![CDATA[')
        self.out.write(data)
        self.out.write(']]>')
