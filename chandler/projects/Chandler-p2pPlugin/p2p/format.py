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

import base64

from itertools import izip

from chandlerdb.util.c import UUID, isuuid, Nil
from chandlerdb.item.c import isitemref
from repository.schema.Kind import Kind
from application import schema
from osaf.sharing import formats, utility
from osaf import pim
from osaf.mail import utils as mailUtils


class CloudXMLDiffFormat(formats.CloudXMLFormat):

    def _importValues(self, dom, view, element, item, stampClasses,
                      activity, stats):

        for valueElement in dom.iterElements(element):
            attrs = dom.getAttributes(valueElement)
            attrName = attrs['name']
            status = attrs.get('status')
                
            if status == 'nil':
                if item.hasLocalAttributeValue(attrName):
                    delattr(item, attrName)
                continue

            attribute = item.itsKind.getAttribute(attrName, False, item)
            otherName = attribute.getAspect('otherName')
            cardinality = attribute.getAspect('cardinality')
            attrType = attribute.getAspect('type')

            # This code depends on attributes having their type set,
            # which might not always be the case. What should be
            # done is to encode the value type into the shared xml
            # itself: 

            if otherName or isinstance(attrType, Kind):
                if cardinality == 'single':
                    for child in dom.iterElements(valueElement):
                        valueItem = self.importProcess(dom, child)
                        if valueItem is not None:
                            setattr(item, attrName, valueItem)

                elif cardinality == 'list':
                    count = 0
                    for child in dom.iterElements(valueElement):
                        valueItem = self.importProcess(dom, child)
                        if valueItem is not None:
                            count += 1
                            item.addValue(attrName, valueItem)
                    if not count:
                        # Only set to an empty ref collection if
                        # attrName is not already an empty ref
                        # collection 
                        needToSet = True
                        if item.hasLocalAttributeValue(attrName):
                            if len(getattr(item, attrName)) == 0:
                                needToSet = False
                        if needToSet:
                            setattr(item, attrName, [])

                elif cardinality == 'dict':
                    pass

            else: # it's a literal

                if cardinality == 'single':
                    mimeType = attrs.get('mimetype')
                    encoding = attrs.get('encoding') or 'utf-8'
                    content = dom.getContent(valueElement)

                    if mimeType: # Lob
                        indexed = mimeType == "text/plain"
                        value = base64.b64decode(content)

                        value = mailUtils.dataToBinary(item, attrName,
                                                       value, mimeType,
                                                       'bz2', indexed)
                        if encoding:
                            value.encoding = encoding
                    else:
                        value = attrType.makeValue(content)

                    setattr(item, attrName, value)

                elif cardinality == 'list':
                    values = []
                    for child in dom.iterElements(valueElement):
    
                        mimeType = dom.getAttribute(child, 'mimetype')
                        if mimeType: # Lob
                            indexed = mimeType == "text/plain"
                            value = base64.b64decode(child.children[0])
                            value = mailUtils.dataToBinary(item, attrName,
                                                           value, mimeType,
                                                           'bz2', indexed)
                            encoding = dom.getAttribute(child, 'encoding')
                            if encoding:
                                value.encoding = encoding

                        else:
                            content = dom.getContent(child)
                            value = attrType.makeValue(content)

                        values.append(value)

                    setattr(item, attrName, values)

                elif cardinality == 'dict':
                    pass

    def importProcess(self, dom, element, item=None,
                      activity=None, stats=None):

        view = self.itsView
        item, stamps, done = self._importItem(dom, view, element,
                                              item, activity, stats)
        if done:
            return item

        try:
            item._share_importing = True
            self._importValues(dom, view, element, item, stamps,
                               activity, stats)
        finally:
            del item._share_importing

        if isinstance(item, pim.ContentItem):
            self._importStamps(item, stamps)

        return item

    def exportProcess(self, dom, key, element, changes, keys):

        view = self.itsView
        kind = view.kindForKey(key)

        attributes = changes.get(key, ())
        if attributes:
            attributes = tuple(attributes[0])

        if keys is None:
            keys = set()

        if key in keys:
            dom.openElement(element, kind.itsName, uuid=key.str64())
            dom.closeElement(element, kind.itsName)
            return None

        keys.add(key)

        pairs = [(name, Nil) for name in attributes]
        pairs.append((pim.Stamp.stamp_types.name, ()))
        values = list(view.findValues(key, *pairs))

        stampClasses = values.pop()
        elementName, classes = self._getElementName(kind, stampClasses)

        attrs = { 'class': classes, 'uuid': key.str64() }
        item = dom.openElement(element, elementName, **attrs)

        for attrName, attrValue in izip(attributes, values):
            if attrValue is Nil:
                dom.openElement(item, 'value', name=attrName, status='nil')
                dom.closeElement(item, 'value')

            else:
                attribute = kind.getAttribute(attrName) 
                attrType = attribute.getAspect('type')
                cardinality = attribute.getAspect('cardinality')
                otherName = attribute.getAspect('otherName', None)

                if otherName:
                    value = dom.openElement(item, 'value', name=attrName)

                    if isuuid(attrValue):
                        self.exportProcess(dom, attrValue, value,
                                           changes, keys)
                    elif cardinality == 'list':
                        for attrKey in attrValue.iterkeys():
                            self.exportProcess(dom, attrKey, value,
                                               changes, keys)

                    dom.closeElement(item, 'value')
                else:
                    if cardinality == 'single':
                        if isitemref(attrValue):
                            value = dom.openElement(item, 'value', name=attrName)
                            attrValue = attrValue.itsUUID
                            self.exportProcess(dom, attrValue, value,
                                               changes, keys)
                            dom.closeElement(item, 'value')
                        else:
                            mimetype, encoding, attrValue = utility.serializeLiteral(attrValue, attrType)

                            attrs = { 'name': attrName }
                            if mimetype:
                                attrs['mimetype'] = mimetype
                            if encoding:
                                attrs['encoding'] = encoding
                                attrValue = unicode(attrValue, encoding)
                            else:
                                attrValue = unicode(attrValue, 'utf-8')

                            dom.openElement(item, 'value',
                                            content=attrValue, **attrs)
                            dom.closeElement(item, 'value')

                    elif cardinality == 'list':
                        value = dom.openElement(item, 'value', name=attrName)
                        for v in attrValue:
                            attrs = {}
                            mimetype, encoding, v = utility.serializeLiteral(v, attrType)

                            if mimetype:
                                attrs['mimetype'] = mimetype
                            if encoding:
                                attrs['encoding'] = encoding
                                v = unicode(v, encoding)
                            else:
                                v = unicode(v, 'utf-8')

                            dom.openElement(value, 'value', content=v, **attrs)
                            dom.closeElement(value, 'value')
                        dom.closeElement(item, 'value')

        dom.closeElement(element, elementName)
