""" Classes used by the repository view
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import OSAF.framework.blocks.ControlBlocks as ControlBlocks

class RepositoryDelegate:
    """ Used by the tree in the repository view
    """
    
    def ElementParent(self, element):
        try:
            return element.getItemParent()
        except AttributeError:
            return None

    def ElementChildren(self, element):
        if element:
            return element
        else:
            return Globals.repository.view

    def ElementCellValues(self, element):
        cellValues = []
        if element == Globals.repository.view:
            cellValues.append ("//")
        else:
            cellValues.append (element.getItemName())
            cellValues.append (str (element.getItemDisplayName()))
            try:
                cellValues.append (element.kind.getItemName())
            except AttributeError:
                cellValues.append ('(kindless)')
            cellValues.append (str (element.getUUID()))
            cellValues.append (str (element.getItemPath()))
        return cellValues

    def ElementHasChildren(self, element):
        if element == Globals.repository.view:
            return True
        else:
            return element.hasChildren()

    def NeedsUpdate(self, notification):
        """
          We need to update the display when any container has
        a child that has been changed. When items are are added
        or modified we can ask for their parent. However, when
        they are deleted we can't access them, so the repository
        sends us their parent.
        """
        try:
            parentUUID = notification.data['parent']
        except KeyError:
            item = Globals.repository.find (notification.data['uuid'])
            parentUUID = item.getItemParent().getUUID()
        counterpart = Globals.repository.find (self.counterpartUUID)
        if counterpart.openedContainers.has_key (parentUUID):
            self.scheduleUpdate = True


class RepositoryItemDetail(ControlBlocks.ItemDetail):

    def getHTMLText(self, item):
        def formatReference(reference):
            """
            Formats the a reference attribute to be clickable, etcetera
            """

            if reference == None:
                return "(None)"

            url = reference.getItemPath()
            if reference.hasAttributeValue('kind'):
                kind = reference.kind.getItemName()
            else:
                kind = "(kindless)"
                
            dn = str(reference.getItemDisplayName())
            
            # Escape < and > for HTML display
            kind = kind.replace("<", "&lt;").replace(">", "&gt;")
            dn = dn.replace("<", "&lt;").replace(">", "&gt;")
            
            return "<a href=\"%(url)s\">%(kind)s: %(dn)s</a>" % locals()

        try:
            displayName = item.getItemDisplayName()
            try:
                kind = item.kind.getItemName()
            except AttributeError:
                kind = "(kindless)"
            
            HTMLText = "<html><body><h5>%s: %s</h5><ul>" % (kind, displayName)
            HTMLText = HTMLText + "<li><b>Path:</b> %s" % item.getItemPath()
            HTMLText = HTMLText + "<li><b>UUID:</b> %s" % item.getUUID()
            HTMLText = HTMLText + "</ul><h5>Attributes</h5><ul>"
    
            # We build tuples (name, formatted) for all value-only, then
            # all reference-only. Then we concatenate the two lists and sort
            # the result, and append that to the HTMLText.
            valueAttr = []
            for k, v in item.iterAttributes(valuesOnly=True):
                if isinstance(v, dict):
                    tmpList = ["<li><b>%s:</b></li><ul>" % k]
                    for attr in v:
                        attrString = str(attr)
                        attrString = attrString.replace("<", "&lt;")
                        attrString = attrString.replace(">", "&gt;")
                        tmpList.append("<li>%s</li>" % attrString)
                    tmpList.append("</ul>")
                    valueAttr.append((k, "".join(tmpList)))
                else:
                    value = str(v)
                    value = value.replace("<", "&lt;")
                    value = value.replace(">", "&gt;")
                    valueAttr.append((k,"<li><b>%s: </b>%s</li>" % (k, value)))
    
            refAttrs = []
            for k, v in item.iterAttributes(referencesOnly=True):
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
