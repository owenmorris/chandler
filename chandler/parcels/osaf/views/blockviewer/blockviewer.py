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

def getItemName (item):
    name = getattr (item, 'blockName', None)
    if name is None:
        method = getattr (type (item), 'getItemDisplayName', None)
        if method is None:
            name = u''
        else:
            name = method (item)
    return name

class BlockItemDetail(ControlBlocks.ItemDetail):

    def getHTMLText(self, item):
        def formatReference(reference):
            """
            Formats the a reference attribute to be clickable, etcetera
            """

            if reference == None:
                return "(None)"

            url = reference.itsPath
            name = getItemName (reference)
            kind = reference.itsKind
            if kind is not None:
                kind = kind.itsName
            else:
                kind = "(kindless)"

            # Escape < and > for HTML display
            kind = kind.replace(u"<", u"&lt;").replace(u">", u"&gt;")
            name = name.replace(u"<", u"&lt;").replace(u">", u"&gt;")

            return u"<a href=\"%(url)s\">%(name)s: %(kind)s</a>" % locals()

        kind = getattr (item.itsKind, 'itsName', None)
        if kind is None:
            kind = "(kindless)"

        HTMLText = u"<html><body><h5>%s: %s</h5><ul>" % (getItemName (item), kind)
        HTMLText = HTMLText + u"<li><b>Path:</b> %s" % item.itsPath
        HTMLText = HTMLText + u"<li><b>UUID:</b> %s" % item.itsUUID
        HTMLText = HTMLText + u"</ul><h5>Attributes</h5><ul>"

        # We build tuples (name, formatted) for all value-only, then
        # all reference-only. Then we concatenate the two lists and sort
        # the result, and append that to the HTMLText.
        valueAttr = []
        for name, value in item.iterAttributeValues(valuesOnly=True):
            if isinstance(value, dict):
                tmpList = [u"<li><b>%s:</b></li><ul>" % name]
                for attr in value:
                    attrString = unicode(attr)
                    attrString = attrString.replace(u"<", u"&lt;")
                    attrString = attrString.replace(u">", u"&gt;")
                    tmpList.append(u"<li>%s</li>" % attrString)
                tmpList.append(u"</ul>")
                valueAttr.append((name, "".join(tmpList)))
            else:
                value = unicode(value)
                value = value.replace(u"<", u"&lt;")
                value = value.replace(u">", u"&gt;")
                valueAttr.append((name,u"<li><b>%s: </b>%s</li>" % (name, value)))

        refAttrs = []
        for name, value in item.iterAttributeValues(referencesOnly=True):
            if (isinstance(value, dict) or
                isinstance(value, list) or
                isinstance(value, RefList)):
                tmpList = [u"<li><b>%s:</b></li><ul>" % name]
                for attr in value:
                    tmpList.append(u"<li>%s</li>" % formatReference(attr))
                tmpList.append(u"</ul>")
                refAttrs.append((name, "".join(tmpList)))
            else:
                value = formatReference(value)
                refAttrs.append((name, u"<li><b>%s: </b>%s</li>" % (name, value)))

        # Finally, try to get the widget, a python attribute, if it's present
        name = 'widget'
        widget = getattr (item, name, None)
        if widget is not None:
            value = unicode (type (widget))
            value = value [value.find ("'")+1 : value.rfind ("'")]
            valueAttr.append((name,u"<li><b>%s: </b>%s</li>" % (name, value)))
            
            if isinstance (widget, wx.Window):
                sizer = widget.GetSizer()
                if sizer is not None:
                    tmpList = [u"<li><b>%s:</b></li><ul>" % "Sizer Items"]
                    for sizerItem in sizer.GetChildren():
                        if sizerItem.IsShown():
                            isShown = u"visible"
                        else:
                            isShown = u"not Shown"
                        value = sizerItem.GetWindow()
                        if value is not None:
                            tmpList.append(u"<li>%s %s</li>" % (formatReference(value.blockItem), isShown))
                        else:
                            value = sizerItem.GetSizer()
                            if value is None:
                                value = sizerItem.GetSpacer()
                            value = unicode (type (item))
                            value = value [value.find ("'")+1 : value.rfind ("'")]
                            tmpList.append(u"<li>%s %s</li>" % value, isShown)
                    tmpList.append(u"</ul>")
                    valueAttr.append((name, "".join(tmpList)))

            allAttrs = refAttrs + valueAttr
            allAttrs.sort()
            dyn_html = "".join([y for x, y in allAttrs])

            HTMLText = u"%s%s</ul></body></html>" % (HTMLText, dyn_html)

        return HTMLText


class BlockDelegate (ControlBlocks.ListDelegate):
    """ Used by the tree in the Block viewer
    """

    def GetElementParent(self, element):
        return getattr (element, "parentBlock", None)

    def GetElementChildren(self, element):
        if element is None:
            return [self.blockItem.findPath('//parcels/osaf/views/main/MainViewRoot')]
        else:
            return element.childrenBlocks

    def GetElementValues(self, element):
        blockName = getattr (element, 'blockName', None)
        if blockName is None:
            blockName = '(anonymous)'
        cellValues = [blockName]

        kind = element.itsKind
        name = getattr (kind, 'itsName', None)
        if name is None:
            cellValues.append ('')
        else:
            cellValues.append (name)

        widget = getattr (element, 'widget', None)
        if widget is None:
            widgetText = "None"
        else:
            widgetText = unicode (type (widget))
            widgetText = widgetText [widgetText.find ("'")+1 : widgetText.rfind ("'")]

        cellValues.append (widgetText)
        cellValues.append (unicode (element.itsUUID))
            
        return cellValues

    def ElementHasChildren(self, element):
        return len (element.childrenBlocks) > 0
