""" Classes used by the repository view
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import osaf.framework.blocks.ControlBlocks as ControlBlocks

class RepositoryDelegate (ControlBlocks.ListDelegate):
    """ Used by the tree in the repository view
    """
    
    def GetElementParent(self, element):
        return element.itsParent

    def GetElementChildren(self, element):
        if element:
            return element.iterChildren()
        else:
            return wx.GetApp().UIRepositoryView

    def GetElementValues(self, element):
        cellValues = [element.itsName or '(anonymous)']
        try:
            cellValues.append (unicode (element.getItemDisplayName()))
        except AttributeError:
            cellValues.append (' ')
        try:
            cellValues.append (element.itsKind.itsName)
        except AttributeError:
            cellValues.append (' ')
        cellValues.append (unicode (element.itsUUID))
        cellValues.append (unicode (element.itsPath))
        return cellValues

    def ElementHasChildren(self, element):
        if element == wx.GetApp().UIRepositoryView:
            return True
        else:
            return element.hasChildren()

    def KindAcceptedByDrop(self):
        return ["Item"] # any item can be Dropped here

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
                
            dn = unicode(reference.getItemDisplayName())
            
            # Escape < and > for HTML display
            kind = kind.replace("<", "&lt;").replace(">", "&gt;")
            dn = dn.replace("<", "&lt;").replace(">", "&gt;")
            
            return "<a href=\"%(url)s\">%(kind)s: %(dn)s</a>" % locals()

        try:
            displayName = item.getItemDisplayName()
            try:
                kind = item.itsKind.itsName
            except AttributeError:
                kind = "(kindless)"
            
            HTMLText = "<html><body><h5>%s: %s</h5><ul>" % (kind, displayName)
            HTMLText = HTMLText + "<li><b>Path:</b> %s" % item.itsPath
            HTMLText = HTMLText + "<li><b>UUID:</b> %s" % item.itsUUID
            HTMLText = HTMLText + "</ul><h5>Attributes</h5><ul>"
    
            # We build tuples (name, formatted) for all value-only, then
            # all reference-only. Then we concatenate the two lists and sort
            # the result, and append that to the HTMLText.
            valueAttr = []
            for k, v in item.iterAttributeValues(valuesOnly=True):
                if isinstance(v, dict):
                    tmpList = ["<li><b>%s:</b></li><ul>" % k]
                    for attr in v:
                        attrString = unicode(attr)
                        attrString = attrString.replace("<", "&lt;")
                        attrString = attrString.replace(">", "&gt;")
                        tmpList.append("<li>%s</li>" % attrString)
                    tmpList.append("</ul>")
                    valueAttr.append((k, "".join(tmpList)))
                else:
                    value = unicode(v)
                    value = value.replace("<", "&lt;")
                    value = value.replace(">", "&gt;")
                    valueAttr.append((k,"<li><b>%s: </b>%s</li>" % (k, value)))
    
            refAttrs = []
            for k, v in item.iterAttributeValues(referencesOnly=True):
                if isinstance(v, dict) or isinstance(v, list):
                    tmpList = ["<li><b>%s:</b></li><ul>" % k]
                    for attr in v:
                        tmpList.append("<li>%s</li>" % formatReference(attr))
                    tmpList.append("</ul>")
                    refAttrs.append((k, "".join(tmpList)))
                else:
                    value = formatReference(v)
                    refAttrs.append((k,"<li><b>%s: </b>%s</li>" % (k, value)))
    
            allAttrs = refAttrs + valueAttr
            allAttrs.sort()
            dyn_html = "".join([y for x, y in allAttrs])
    
            HTMLText = "%s%s</ul></body></html>" % (HTMLText, dyn_html)
        except:
            HTMLText = "<html><body><h5></h5></body></html>"

        return HTMLText


class CPIADelegate (ControlBlocks.ListDelegate):
    """ Used by the tree in the repository view
    """
    
    def GetElementParent(self, element):
        return element.parentBlock

    def GetElementChildren(self, element):
        if element:
            return element.childrenBlocks
        else:
            return self.blockItem.findPath('//userdata/MainViewRoot')

    def GetElementValues(self, element):
        try:
            blockName = element.blockName
        except AttributeError:
            blockName = 'None'
        cellValues = [blockName]

        try:
            cellValues.append (element.itsKind.itsName)
        except AttributeError:
            cellValues.append (' ')

        try:
            cellValues.append (unicode (element.getItemDisplayName()))
        except AttributeError:
            cellValues.append (' ')
        cellValues.append (unicode (element.itsUUID))
        cellValues.append (unicode (element.itsPath))
        return cellValues

    def ElementHasChildren(self, element):
        return len (element.childrenBlocks) > 0
