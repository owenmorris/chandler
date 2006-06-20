#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import sys, traceback

from elementtree.SimpleXMLWriter import XMLWriter
from xml.sax import InputSource, make_parser, handler
from cStringIO import StringIO


class SAXError(Exception):
    pass

class ParserError(SAXError):
    pass


# handler class are old-style
# protocol as per expatreader.py
class LexicalHandler:

    def comment(self, data):
        pass

    def startCDATA(self):
        pass

    def endCDATA(self):
        pass

    def startDTD(self, doctypeName, systemId, publicId, hasInternalSubset):
        pass

    def endDTD(self):
        pass


class SAXHandler(object,
                 handler.ContentHandler, handler.ErrorHandler, LexicalHandler):

    def __init__(self):

        self._cdata = False

    def startCDATA(self):

        self._cdata = True

    def endCDATA(self):

        self._cdata = False


class ContentHandler(SAXHandler):

    def __init__(self):

        SAXHandler.__init__(self)
        self.exception = None

    def saveException(self):

        type, value, stack = sys.exc_info()
        self.exception = traceback.format_exception(type, value, stack)

    def errorOccurred(self):

        return self.exception is not None

    def parseSource(self, inputSource):

        parser = make_parser()
        parser.setContentHandler(self)
        parser.setErrorHandler(self)
        parser.setProperty(handler.property_lexical_handler, self)

        parser.parse(inputSource)

        if self.errorOccurred():
            raise self.saxError()

    def parse(self, xml):

        input = InputSource()
        input.setByteStream(StringIO(xml))
        self.parseSource(input)
        
    def parseFile(self, inputFile):

        input = InputSource(inputFile)
        input.setByteStream(file(inputFile))
        self.parseSource(input)
        
    def saxError(self):

        try:
            buffer = StringIO()
            buffer.write("(nested exception traceback below)\n\n")
            for text in self.exception:
                buffer.write(text)

            return SAXError(buffer.getvalue())

        finally:
            buffer.close()


class XMLGenerator(object, XMLWriter):

    def __init__(self, out, encoding='utf-8'):

        XMLWriter.__init__(self, out, encoding)
        self.out = out
        self.encoding = encoding

    def getOutputStream(self):

        return self.out

    def write(self, data):

        self._XMLWriter__flush()
        self._XMLWriter__write(data)

    def startDocument(self):
        
        self.declaration()

    def endDocument(self):

        self.flush()

    def startElement(self, tag, attrs):

        self.start(tag, attrs)

    def endElement(self, tag):

        self.end(tag)
    
    def characters(self, data):

        if data:
            self.data(data)

    def cdataSection(self, data, start=True, end=True):

        if data and isinstance(data, unicode):
            data = data.encode(self.encoding)

        if start:
            self.write('<![CDATA[')
        if data:
            self.write(data)
        if end:
            self.write(']]>')


class XMLPrettyGenerator(XMLGenerator):

    def __init__(self, generator):

        self.generator = generator
        self._indent = '  '
        self._indents = 0
        self._nl = False
        
        super(XMLPrettyGenerator, self).__init__(generator.getOutputStream())

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

        if self._cdata:
            self.cdataBlock(self, data)
        elif self.output():
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
