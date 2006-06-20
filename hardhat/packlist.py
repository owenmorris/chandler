#!/usr/bin/env python

#   Copyright (c) 2002-2006 Open Source Applications Foundation
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


import sys, re, os.path, xml.sax


class packlist(list, xml.sax.ContentHandler):
    'A list and SAX ContentHandler implementation listing packs.'

    def __init__(self, path):

        super(list, self).__init__()
        
        self.cwd = [ os.path.dirname(path) ]
        self.tagAttrs = []
        xml.sax.parse(path, self)

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
