#!/usr/bin/env python

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, re, os.path, xml.sax


class packlist(list, xml.sax.ContentHandler):
    'A list and SAX ContentHandler implementation listing packs.'

    def __init__(self, path):

        super(list, self).__init__(self)
        
        self.path = path
        self.cwd = [ os.path.dirname(path) ]

        xml.sax.parse(path, self)

    def startDocument(self):

        self.tagAttrs = []

    def startElement(self, tag, attrs):

        method = getattr(packlist, tag + 'Start', None)
        if method is not None:
            method(self, attrs)
            
        self.tagAttrs.append(attrs)

    def endElement(self, tag):

        attrs = self.tagAttrs.pop()

        method = getattr(packlist, tag + 'End', None)
        if method is not None:
            method(self, attrs)

    def packStart(self, attrs):

        if attrs.has_key('cwd'):
            self.cwd[-1] = os.path.join(self.cwd[-1], attrs['cwd'])

    def cwdStart(self, attrs):

        self.cwd.append(os.path.join(self.cwd[-1], attrs['path']))

    def cwdEnd(self, attrs):

        self.cwd.pop()

    def itemStart(self, attrs):

        if attrs.has_key('file'):
            self.append(os.path.join(self.cwd[-1], attrs['file']))
        elif attrs.has_key('files'):
            pattern = '^' + attrs['files'] + '$'
            pattern = pattern.replace('.', '\\.').replace('*', '.*')
            exp = re.compile(pattern)

            for file in os.listdir(self.cwd[-1]):
                if exp.match(file):
                    self.append(os.path.join(self.cwd[-1], file))
            
        if attrs.has_key('cwd'):
            self.cwd.append(os.path.join(self.cwd[-1], attrs['cwd']))

    def itemEnd(self, attrs):

        if attrs.has_key('cwd'):
            self.cwd.pop()


if __name__ == "__main__":
    for path in packlist(sys.argv[1]):
        print path
