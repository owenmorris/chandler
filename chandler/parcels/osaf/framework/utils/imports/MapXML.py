"""Parse XML file to create a mapping object."""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import ImportMap
import libxml2

START=1
END=15

class MapXML(object):
    """Parse XML file to create a mapping object.
    
    @ivar path: The path to the xml mapping file.
    
    """
    def __init__(self, path):
        self.path=path
        self.emptyDates=[]
        self.lastXMLAttr=None
        self.lastTag=None
        self.reader=None
        self.stack=[ImportMap.AttributeCollection()]

    def pushCollection(self):
        """Push an L{AttributeCollection} onto the stack."""
        c=ImportMap.AttributeCollection()
        c.parentMap=self.stack[-1]
        if self.lastTag=='ListItem':
            c.name=c.parentMap.name
        elif self.lastTag=='Attribute':
            c.name=self.lastXMLAttr
        self.stack.append(c)

    def pushList(self):
        """Push a L{ListValue} onto the stack."""
        l=ImportMap.ListValue()
        l.name=self.lastXMLAttr
        l.parentMap=self.stack[-1]
        self.stack.append(l)

    def pop(self):
        """Pop an L{ImportMap} off the stack, store it in its parent."""
        listItem=self.stack.pop()
        last=self.stack[-1]
        last.maps.append(listItem)

    def processNode(self, view):
        name=self.reader.Name()
        type=self.reader.NodeType()
        if name == 'Attribute':
            if type == START:
                if self.lastTag in ['Attribute', 'ListItem']:
                    self.pushCollection()
                self.saveNode()
            elif type == END:
                if self.lastTag:
                    self.emptySavedNode()
                else:
                    self.pop()
        elif name == 'ListItem':
            if type == START:
                self.saveNode()
            elif type == END:
                if self.lastTag:
                    self.emptySavedNode()
                else:
                    self.pop()
        elif name == 'List':
            if type == START:
                self.pushList()
                self.emptySavedNode()
        else:
            expandNodes=['RootKind','EmptyDate','StringKey','Concatenate',
                         'DateKey', 'If']
            if name in expandNodes:
                node = self.reader.Expand()
                if name == 'RootKind':
                    kind=view.findPath(node.getContent())
                    self.stack[0].kind=kind
                elif name == 'EmptyDate':
                    self.emptyDates.append(node.getContent())
                elif name == 'StringKey':
                    key=node.getContent()
                    name=self.lastXMLAttr
                    parent=self.stack[-1]
                    if name == None:#list of strings case
                        name = parent.name
                    self.stack.append(ImportMap.StringValue(key, name, parent))
                elif name == 'DateKey':
                    key=node.getContent()
                    name=self.lastXMLAttr
                    d=ImportMap.DateValue(key, name, self.emptyDates)
                    self.stack.append(d)
                elif name == 'If':
                    key=node.xpathEval("TestKey")[0].getContent()
                    value=node.xpathEval("Constant")[0].getContent()
                    name=self.lastXMLAttr
                    self.stack.append(ImportMap.CondValue(key, name, value))
                elif name == 'Concatenate':
                    keys=[i.getContent() for i in node.xpathEval("StringKey")]
                    name=self.lastXMLAttr
                    self.stack.append(ImportMap.ConcatKeys(keys, name))
                self.emptySavedNode()
                self.reader.Next()
                   
    def saveNode(self):
        self.lastTag=self.reader.Name()
        self.reader.MoveToNextAttribute()
        self.lastXMLAttr=self.reader.Value()

    def emptySavedNode(self):
        self.lastTag=None
        self.lastXMLAttr=None
        
    def streamFile(self, view):
        """Open file, process important Nodes.
        
        return: Returns None if the self.path isn't a readable file, or if
        if there's a parsing error.
        rtype:L{ImportMap.ImportMap}
        
        """
        try:
            self.reader = libxml2.newTextReaderFilename(self.path)
            #the reader should be garbage collected, doesn't need to be freed
        except:
            print "unable to open %s" % (self.path)
            return None
    
        ret = self.reader.Read()
        while ret == 1:
            if self.reader.NodeType() in [START, END]:
                self.processNode(view)
            ret = self.reader.Read()
    
        if ret != 0:
            print "%s : failed to parse" % (self.path)
            return None
        return self.stack[0]
    
"""#debugging
if __name__ == "__main__":
    testXML=MapXML('outlook2000.xml')
    ## add repository open code here
    testXML.streamFile(view)
    def walk(x, level=0):
        if type(x)==list:
            for m in x:
                walk(m, level)
        else:
            print " - "*level+str(x.name)
            if hasattr(x, 'maps') and x.maps:
                walk(x.maps, level+1)
    walk(testXML.stack[0])
    print [i.name for i in testXML.stack[0].maps]
"""
