
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, traceback

from libxml2mod import xmlEncodeSpecialChars as escape
from libxml2 import createPushParser, SAXParseFile
from cStringIO import StringIO


class SAXError(Exception):
    pass

class ParserError(SAXError):
    pass


class SAXCallback(object):
    """
    Base class for SAX handlers.

    Source was imported from libxml2 so that this class extends object.
    """

    def startDocument(self):
        """
        Called at the start of the document.
        """
        pass

    def endDocument(self):
        """
        Called at the end of the document.
        """
        pass

    def startElement(self, tag, attrs):
        """
        Called at the start of every element, tag is the name of
        the element, attrs is a dictionary of the element's attributes.
        """
        pass

    def endElement(self, tag):
        """
        Called at the start of every element, tag is the name of the element.
        """
        pass

    def characters(self, data):
        """
        Called when character data have been read, data is the string
        containing the data, multiple consecutive characters() callback
        are possible.
        """
        pass

    def cdataBlock(self, data):
        """
        Called when CDATA section have been read, data is the string
        containing the data, multiple consecutive cdataBlock() callback
        are possible.
        """
        pass

    def reference(self, name):
        """
        Called when an entity reference has been found.
        """
        pass

    def ignorableWhitespace(self, data):
        """
        Called when potentially ignorable white spaces have been found.
        """
        pass

    def processingInstruction(self, target, data):
        """
        Called when a PI has been found, target contains the PI name and
        data is the associated data in the PI.
        """
        pass

    def comment(self, content):
        """
        Called when a comment has been found, content contains the comment.
        """
        pass

    def externalSubset(self, name, externalID, systemID):
        """
        Called when a DOCTYPE declaration has been found, name is the
        DTD name and externalID, systemID are the DTD public and system
        identifier for that DTd if available.
        """
        pass

    def internalSubset(self, name, externalID, systemID):
        """
        Called when a DOCTYPE declaration has been found, name is the
        DTD name and externalID, systemID are the DTD public and system
        identifier for that DTD if available.
        """
        pass

    def entityDecl(self, name, type, externalID, systemID, content):
        """
        Called when an ENTITY declaration has been found, name is the
        entity name and externalID, systemID are the entity public and
        system identifier for that entity if available, type indicates
        the entity type, and content reports it's string content.
        """
        pass

    def notationDecl(self, name, externalID, systemID):
        """
        Called when an NOTATION declaration has been found, name is the
        notation name and externalID, systemID are the notation public and
        system identifier for that notation if available.
        """
        pass

    def attributeDecl(self, elem, name, type, defi, defaultValue, nameList):
        """
        Called when an ATTRIBUTE definition has been found.
        """
        pass

    def elementDecl(self, name, type, content):
        """
        Called when an ELEMENT definition has been found.
        """
        pass

    def entityDecl(self, name, publicId, systemID, notationName):
        """
        Called when an unparsed ENTITY declaration has been found,
        name is the entity name and publicId,, systemID are the entity
        public and system identifier for that entity if available,
        and notationName indicate the associated NOTATION.
        """
        pass

    def warning(self, msg):
        print msg

    def error(self, msg):
        raise ParserError, msg

    def fatalError(self, msg):
        raise ParserError, msg


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

    def parse(self, xml):

        createPushParser(self, xml, len(xml), 'filter').parseChunk('', 0, 1)
        if self.errorOccurred():
            raise self.saxError()
        
    def parseFile(self, file):

        SAXParseFile(self, file, 0)
        if self.errorOccurred():
            raise self.saxError()
        
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

    def getOutputStream(self):

        return self.out

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

        if data:
            if isinstance(data, unicode):
                data = data.encode(self.encoding)

            self.out.write(escape(None, data))

    def cdataSection(self, data, start=True, end=True):

        if data and isinstance(data, unicode):
            data = data.encode(self.encoding)

        if start:
            self.out.write('<![CDATA[')
        if data:
            self.out.write(data)
        if end:
            self.out.write(']]>')


class XMLPrettyGenerator(XMLGenerator):

    def __init__(self, generator):

        self.generator = generator
        self._indent = '  '
        self._indents = 0
        self._nl = False
        
        super(XMLPrettyGenerator, self).__init__(None)

    def getOutputStream(self):

        return self.generator.getOutputStream()

    def write(self, data):

        self.generator.write(data)

    def startDocument(self):

        self._indents = 0
        self.generator.startDocument()

    def endDocument(self):

        self.generator.endDocument()

    def startElement(self, tag, attrs):

        self.write('\n')
        for i in xrange(self._indents):
            self.write(self._indent)
        self.generator.startElement(tag, attrs)
        self._indents += 1

    def endElement(self, tag):

        self._indents -= 1
        if self._nl:
            self.write('\n')
            for i in xrange(self._indents):
                self.write(self._indent)
        self.generator.endElement(tag)
        self._nl = True
        
    def characters(self, data):

        self.generator.characters(data)
        self._nl = False

    def cdataSection(self, data, start=True, end=True):

        self.generator.cdataSection(data, start, end)
        self._nl = False


class XMLFilter(ContentHandler):

    def __init__(self, generator, *tags):

        ContentHandler.__init__(self)

        self.generator = generator
        self.tags = tags
        self.foundTag = 0
        self.cdata = False

    def getGenerator(self):

        return self.generator

    def output(self):

        raise NotImplementedError, 'XMLFilter.output'

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
