""" Classes used by the repository view
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 200 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.blocks.ControlBlocks as ControlBlocks

class RepositoryDelegate:
    """ Used by the tree in the repository view
    """
    
    def ElementParent(self, element):
        return element.itsParent

    def ElementChildren(self, element):
        if element:
            return element
        else:
            return Globals.repository.view

    def ElementCellValues(self, element):
        cellValues = [element.itsName]
        if True or element != Globals.repository.view:
            try:
                cellValues.append (str (element.getItemDisplayName()))
            except AttributeError:
                cellValues.append ('')
            try:
                cellValues.append (element.itsKind.itsName)
            except AttributeError:
                cellValues.append ('')
            cellValues.append (str (element.itsUUID))
            cellValues.append (str (element.itsPath))
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

            try:
                parent = item.itsParent
            except AttributeError:
                return

            parentUUID = parent.itsUUID

        counterpart = Globals.repository.find (self.blockUUID)
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

            url = reference.itsPath
            kind = reference.itsKind
            if kind is not None:
                kind = kind.itsName
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
