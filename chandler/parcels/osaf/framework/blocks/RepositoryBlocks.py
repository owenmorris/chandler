__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Block import *
from ContainerBlocks import *
from ControlBlocks import *
from Node import Node
from repository.util.UUID import UUID
from OSAF.framework.notifications.Notification import Notification
from wxPython.wx import *
from wxPython.html import *


class wxItemDetail(wxHtmlWindow):
    def OnLinkClicked(self, wx_linkinfo):
        event = Globals.repository.find('//parcels/OSAF/framework/blocks/Events/SelectionChanged')
        notification = Notification(event, None, None)
        item = Globals.repository.find(wx_linkinfo.GetHref())
        notification.SetData ({'item':item, 'type':'Normal'})
        Globals.notificationManager.PostNotification (notification)

    def SynchronizeFramework(self):
        def formatReference(reference):
            """
              Formats the a reference attribute to be clickable, etcetera
            """
            url = reference.getItemPath()
            if reference.hasAttributeValue('kind'):
                kind = reference.kind.getItemName()
            else:
                kind = "(kindless)"
            # Originally I was masking the fallback to itemName here just like in
            # the listview, but that doesn't work for many of the more primitive
            # repository items, so I stopped doing that.
            dn = str(reference.getItemDisplayName())
    
            # Escape < and > for HTML display
            kind = kind.replace("<", "&lt;").replace(">", "&gt;")
            dn = dn.replace("<", "&lt;").replace(">", "&gt;")
    
            return "<a href=\"%(url)s\">%(kind)s: %(dn)s</a>" % locals()

        counterpart = Globals.repository.find (self.counterpartUUID)
        item = Globals.repository.find (counterpart.selection)
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
    
        self.SetPage(HTMLText)


class ItemDetail(HTML):
    def renderOneBlock (self, parent, parentWindow):
        htmlWindow = wxItemDetail(parentWindow,
                                Block.getwxID(self),
                                wxDefaultPosition,
                                (self.minimumSize.width, self.minimumSize.height))
        self.getParentBlock(parentWindow).addToContainer(parent,
                                                         htmlWindow,
                                                         self.stretchFactor,
                                                         self.Calculate_wxFlag(),
                                                         self.Calculate_wxBorder())
        return htmlWindow, None, None

    def OnSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWindow counterpart.
        """
        item = notification.data['item']
        self.selection = item.getUUID()
        wxWindow = Globals.association[self.getUUID()]
        wxWindow.SynchronizeFramework ()

