""" Repository Viewer. Creates a view of the entire repository

    Creates a tree:
        <python class of thing>   :    <thing url>
           <attribute url>        :    <attribute value>
    If <attribute value> is a thing, will recursively add a subtree.
    If <attribute value> is a dict or a list, will add subtree.
     
    @@@ Note: The viewer is vulnerable to cycles (we currently don't
        have any in the data). Also, builds up a big tree for the
        whole repository, so the view can be kind of slow to build.
"""
__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from wxPython.wx import *
from wxPython.xrc import *

from persistence.list import PersistentList
from persistence.dict import PersistentDict

from application.repository.Repository import Repository
from application.repository.Thing import Thing
from application.SplashScreen import SplashScreen
from application.ViewerParcel import *

from MultipleColumnTreeCtrl import MultipleColumnTreeCtrl

class RepositoryView(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__ (self)
        
class wxRepositoryView(wxViewerParcel):
    def OnInit(self):
        """Initialize the repository view parcel. This method is called
           when the wxRepositoryView is created -- we use the opportunity
           to hook up menus, buttons, other controls.
        """
        self.viewTable = false
        repository = Repository()

        self.treeCtrl = MultipleColumnTreeCtrl(self, 2, ['Key', 'Value'])
        
        self.container = wxBoxSizer(wxVERTICAL)
        
        self.font = wxFont(18, wxSWISS, wxNORMAL, wxNORMAL, false, "Arial")

        self.title = wxStaticText(self, -1, _("Repository"))
        self.title.SetFont(self.font)
        self.container.Add(self.title, 0, wxEXPAND)
        self.container.Add(self.treeCtrl, 1, wxEXPAND)
        self.SetSizerAndFit(self.container)

        root = self.treeCtrl.AddNewRoot(self.GetItemText(repository.thingList, 'Repository'))
        for item in repository.thingList:
            itemId = self.treeCtrl.AddNewItem(root, str(item.__module__), [item.GetURL()])
            self.AddAttributes(itemId, item)
            
        self.treeCtrl.Expand(root)
        EVT_MENU(self, XRCID('ViewType'), self.OnToggleViewType)
        EVT_MENU(self, XRCID('AboutRepository'), self.OnAboutRepository)
        
    def AddAttributes(self, attrId, item):
        for key in item.keys():
            element = item[key]
            if isinstance(element, Thing):
                newId = self.treeCtrl.AddNewItem(attrId, key, [element.GetURL()])
                # @@@ FIXME: Note: cycles are possible!
                self.AddAttributes(newId, element)
            elif isinstance(element, types.ListType) or isinstance(element, PersistentList):
                self.AddListItem(element, attrId, key)
            elif isinstance(element, types.TupleType):
                self.AddTupleType(element, attrId, key)
            elif isinstance(element, types.DictType) or isinstance(element, PersistentDict):
                self.AddDictItem(element, attrId, key)
            else:
                self.treeCtrl.AddNewItem(attrId, key, [str(element)])

    def AddListItem(self, list, parent, key):
        value = self.GetItemText(list, 'List')
        listId = self.treeCtrl.AddNewItem(parent, key, [value])
#        listId = self.treeCtrl.AddNewItem(parent, value, str(list))
        indexCounter = 0
        for element in list:
            # @@@ FIXME: Note: cycles are possible!
            if (isinstance(element, Thing)):
                newId = self.treeCtrl.AddNewItem(listId, str(element.__module__), [element.GetURL()])
                self.AddAttributes(newId, element)
            else:
                self.treeCtrl.AddNewItem(listId, '[%d]' % (indexCounter), [str(element)])
            indexCounter += 1        
        
    def AddTupleItem(self, tuple, parent, key):
        value = self.GetItemText(tuple, 'Tuple')
        tupleId = self.treeCtrl.AddNewItem(parent, key, [value])
#       tupleId = self.treeCtrl.AddNewItem(parent, value, str(tuple))
        indexCounter = 0
        for element in tuple:
            self.treeCtrl.AddNewItem(tupleId, '[%d]' % (indexCounter), [str(element)])
            indexCounter += 1        
    
    def AddDictItem(self, dict, parent, key):
        value = self.GetItemText(dict, 'Dict')
        dictId = self.treeCtrl.AddNewItem(parent, key, [value])
#        dictId = self.treeCtrl.AddNewItem(parent, value, str(dict))
        for dictKey in dict.keys():
            self.treeCtrl.AddNewItem(dictId, str(dictKey), [str(dict[dictKey])])

    def AddObjectItem(self, object, parent, key):
        value = 'Object'
        objectId = self.treeCtrl.AddNewItem(parent, key, [value])
#        objectId = self.treeCtrl.AddNewItem(parent, value, str(object))
        for dictKey in object.__dict__.keys():
            self.treeCtrl.AddNewItem(objectId, str(dictKey), [str(object.__dict__[dictKey])])

    def GetItemText(self, item, itemTypeName):
        if len(item) == 1:
            itemText = 'item'
        else:
            itemText = 'items'
        return itemTypeName + ' (%d %s):' % (len(item), itemText)
            
    def OnToggleViewType(self, event):
        """
          Not yet implemented.  Will toggle between viewing the data as a tree
        control and a table.
        """
        self.viewTable = not self.viewTable

    def OnAboutRepository(self, event):
        pageLocation = "parcels" + os.sep + "repository" + os.sep + "AboutRepository.html"
        infoPage = SplashScreen(self, _("About Repository"), pageLocation, false)
        if infoPage.ShowModal():
            infoPage.Destroy()
        