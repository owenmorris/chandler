
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, traceback

from libxml2mod import xmlEncodeSpecialChars as escape
from libxml2 import SAXCallback, createPushParser
from cStringIO import StringIO


class SAXError(Exception):
    pass


class ContentHandler(SAXCallback):

    def __init__(self):

        self.exception = None
    
    def cdataBlock(self, data):
        
        self.characters(data)

    def saveException(self):

        type, value, stack = sys.exc_info()
        self.exception = traceback.format_exception(type, value, stack)

    def errorOccurred(self):

        return self.exception is not None

    def saxError(self):

        try:
            buffer = StringIO()
            buffer.write("(nested exception traceback below)\n\n")
            for text in self.exception:
                buffer.write(text)

            return SAXError(buffer.getvalue())

        finally:
            buffer.close()


class XMLGenerator(object):

    def __init__(self, out, encoding='utf-8'):

        self.out = out
        self.encoding = encoding

    def write(self, data):

        self.out.write(data)

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


class XMLFilter(ContentHandler):

    def __init__(self, generator, *tags):

        self.generator = generator
        self.tags = tags
        self.foundTag = 0
        self.cdata = False

    def output(self):

        raise NotImplementedError, 'XMLFilter.output'

    def parse(self, xml):

        createPushParser(self, xml, len(xml), 'filter').parseChunk('', 0, 1)
        
    def endDocument(self):

        if self.cdata:
            self.generator.write(']]>')
            self.cdata = False

    def startElement(self, tag, attrs):

        if self.cdata:
            self.generator.write(']]>')
            self.cdata = False

        if tag in self.tags:
            self.foundTag += 1
        if self.output():
            self.generator.startElement(tag, attrs)

    def endElement(self, tag):

        if self.output():
            if self.cdata:
                self.generator.write(']]>')
                self.cdata = False
            self.generator.endElement(tag)
        if tag in self.tags:
            self.foundTag -= 1

    def characters(self, data):

        if self.output():
            self.generator.characters(data)

    def cdataBlock(self, data):
        
        if self.output():
            if not self.cdata:
                self.generator.write('<![CDATA[')
                self.cdata = True
            self.generator.write(data)

class XMLOffFilter(XMLFilter):

    def output(self):
        return not self.foundTag

class XMLOnFilter(XMLFilter):

    def output(self):
        return self.foundTag

class XMLThruFilter(XMLFilter):

    def output(self):
        return True
