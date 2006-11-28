#   Copyright (c) 2004-2006 Open Source Applications Foundation
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


""" Classes used by the repository view
"""

import wx
import osaf.framework.blocks.ControlBlocks as ControlBlocks

from repository.item.RefCollections import RefList

class RepositoryDelegate (ControlBlocks.ListDelegate):
    """ Used by the tree in the repository view
    """
    
    def GetElementParent(self, element):
        return element.itsParent

    def GetElementChildren(self, element):
        if element is None:
            return [wx.GetApp().UIRepositoryView]
        else:
            return element.iterChildren()

    def GetElementValues(self, element):
        cellValues = [element.itsName or '(anonymous)']

        name = getattr (element, 'blockName', getattr (element, 'displayName', u""))
        cellValues.append (name)

        name = u''
        kind = getattr (element, 'itsKind', None)
        if kind is not None:
            itsName = getattr (kind, 'itsName', None)
            if itsName is not None:
                name = itsName
        cellValues.append (name)

        cellValues.append (unicode (element.itsUUID))
        cellValues.append (unicode (element.itsPath))
        return cellValues

    def ElementHasChildren(self, element):
        if element == wx.GetApp().UIRepositoryView:
            return True
        else:
            return element.hasChildren()

class RepositoryItemDetail(ControlBlocks.ItemDetail):

    def getHTMLText(self, item):
        def formatReference(reference):
            """
            Formats the a reference attribute to be clickable, etcetera
            """

            if reference == None:
                return "(None)"

            url = reference.itsPath
            kind = reference.itsKind
            if kind is not None:
                kind = kind.itsName
            else:
                kind = "(kindless)"

            dn = getattr(reference, 'displayName', reference.itsName) or reference.itsUUID.str64()

            # Escape < and > for HTML display
            kind = kind.replace(u"<", u"&lt;").replace(u">", u"&gt;")
            dn = dn.replace(u"<", u"&lt;").replace(u">", u"&gt;")

            return u"<a href=\"%(url)s\">%(kind)s: %(dn)s</a>" % locals()

        try:
            displayName = getattr(item, 'displayName', item.itsName) or item.itsUUID.str64()
            if item.itsKind is None:
                kind = "(kindless)"
            else:
                kind = item.itsKind.itsName

            HTMLText = u"<html><body><h5>%s: %s</h5><ul>" % (kind, displayName)
            HTMLText = HTMLText + u"<li><b>Path:</b> %s" % item.itsPath
            HTMLText = HTMLText + u"<li><b>UUID:</b> %s" % item.itsUUID
            HTMLText = HTMLText + u"</ul><h5>Attributes</h5><ul>"

            # We build tuples (name, formatted) for all value-only, then
            # all reference-only. Then we concatenate the two lists and sort
            # the result, and append that to the HTMLText.
            valueAttr = []
            for k, v in item.iterAttributeValues(valuesOnly=True):
                if isinstance(v, dict):
                    tmpList = [u"<li><b>%s:</b></li><ul>" % k]
                    for attr in v:
                        attrString = unicode(attr)
                        attrString = attrString.replace(u"<", u"&lt;")
                        attrString = attrString.replace(u">", u"&gt;")
                        tmpList.append(u"<li>%s</li>" % attrString)
                    tmpList.append(u"</ul>")
                    valueAttr.append((k, "".join(tmpList)))
                else:
                    value = unicode(v)
                    value = value.replace(u"<", u"&lt;")
                    value = value.replace(u">", u"&gt;")
                    valueAttr.append((k,u"<li><b>%s: </b>%s</li>" % (k, value)))

            refAttrs = []
            for k, v in item.iterAttributeValues(referencesOnly=True):
                if (isinstance(v, dict) or
                    isinstance(v, list) or
                    isinstance(v, RefList)):
                    tmpList = [u"<li><b>%s:</b></li><ul>" % k]
                    for attr in v:
                        tmpList.append(u"<li>%s</li>" % formatReference(attr))
                    tmpList.append(u"</ul>")
                    refAttrs.append((k, "".join(tmpList)))
                else:
                    value = formatReference(v)
                    refAttrs.append((k, u"<li><b>%s: </b>%s</li>" % (k, value)))

            allAttrs = refAttrs + valueAttr
            allAttrs.sort()
            dyn_html = "".join([y for x, y in allAttrs])

            HTMLText = u"%s%s</ul></body></html>" % (HTMLText, dyn_html)
        except:
            HTMLText = u"<html><body><h5></h5></body></html>"

        return HTMLText
