""" 
The ContactsView class is the main class for the Contacts parcel
"""

__revision__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002, 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import time

from wxPython.wx import *
from wxPython.xrc import *

from application.Application import app
from application.ViewerParcel import *
from application.repository.Namespace import chandler
from application.repository.Repository import Repository
from application.PresencePanel import *

from persistence import Persistent
from persistence.list import PersistentList

from application.repository.Contact import Contact

from OSAF.contacts.ContactsControlBar import ContactsControlBar
from OSAF.contacts.ContactsIndexView import ContactsIndexView
from OSAF.contacts.ContactsSingleContactView import *

from OSAF.contacts.ContactViewInfo import *
from OSAF.contacts.ContactsDialog import *
from OSAF.contacts.ContactsModel import *
from OSAF.contacts.ContactsTest import *

from application.SplashScreen import SplashScreen

class ContactsViewer(ViewerParcel):
    def __init__(self):
        ViewerParcel.__init__ (self)
        
        # keep a dictionary of the views
        self.views = PersistentList()
        self.InitializeViews()
        
        # keep some preferences in the persistent object
        self.useOneNameField = true
        self.queryOpen = false
        
        self.currentViewTypeIndex = 0
        self.currentViewIndex = 0
        self.currentZoomIndex = 1

        self.lastContactType = None
        self.lastImageDirectory = None

    # set up the initial, built-in views here
    def InitializeViews(self):

        # get the URL tree and add the base URL
        tree = app.model.URLTree
        tree.AddURL(self, 'Contacts')
        
        # add the 'All Contacts' view
        description = _('Display all contacts in the local repository.')
        view = ContactViewInfo(chandler.Contact, None, _('All Contacts'), description)
        self.views.append(view)
        tree.AddURL(self, 'Contacts/All Contacts')
        
        # add the 'Coworkers' view
        description = _('Display all contacts that are Coworkers')
        condition = FilterCondition(None, 'hasgroup', 'Coworkers', true)
        view = ContactViewInfo(chandler.Contact, [condition], _('Coworkers'), description)
        self.views.append(view)
        tree.AddURL(self, 'Contacts/Coworkers')
        
        # add the 'Companies' view
        description = _('Display all contacts that are companies')
        condition = FilterCondition(chandler.contactType, 'equals', 'Company', true)
        view = ContactViewInfo(chandler.Contact, [condition], _('Companies'), description)
        self.views.append(view)
        tree.AddURL(self, 'Contacts/Companies')
    
    # navigate to the view specified by the url, using the repository
    # specified by the remoteAddress; use the local repository for None
    def GoToURL(self, remoteAddress, url):
        ViewerParcel.GoToURL(self, remoteAddress, url)
        viewer = app.association[id(self)]
        viewer.GoToURL(remoteAddress, url)
        return true
    
    # return a list of accessible views (for now, ones that are public)
    def GetAccessibleViews(self, who):
        accessibleViews = []
        for view in self.views:
            if view.sharingPolicy == 'public':
                accessibleViews.append('Contacts/' + view.title)
        return accessibleViews

    # add the objects in the passed-in list to the objectlist,
    # and display them.  Pass it on to the wxViewer to do the work
    def AddObjectsToView(self, url, objectList, lastFlag):
       viewer = app.association[id(self)]
       viewer.AddObjectsToView(url, objectList, lastFlag)
        
    # given a url, return the corresponding viewinfo object
    def GetViewFromURL(self, url):
        viewList = self.views
        mappedurl = url.lower()
        for view in viewList:
            viewURL = view.GetURL()
            if viewURL.lower() == mappedurl:
                return view
        return None

    # determine if the passed-in jabberID has access to the passed in url
    # FIXME: for now, it only knows about 'public'; clean this up and reconcile with AllowToAccess
    # when a have a real sharing policy class
    def HasPermission(self, jabberID, url):
        viewInfo = self.GetViewFromURL(url)
        if viewInfo != None:
            return viewInfo.sharingPolicy == 'public'
        return false
    
    # interpret sharing policy to determine if the passed in ID is allowed
    # to access the passed in item.  This is similar to HasPermission above,
    # but at the item level instead of the view level
    # FIXME: for now, it only knows about 'public'. The more sophisticated
    # code awaits a sharing policy class
    def AllowedToAccess(self, item, jabberID):
        sharingPolicy = item.GetAttribute(chandler.sharing)
        return sharingPolicy == 'public'

    # return a list of objects from the view specified by the url.  Note
    # that it might not be the current view.
    def GetViewObjects(self, url, jabberID):
        contactList = []
       
        # select the view based on the url
        viewInfo = self.GetViewFromURL(url)
        if viewInfo != None:
            # build the objectlist by iterating through the local repository
            repository = Repository()
            for item in repository.thingList:
                # let the view filter according to its query
                if viewInfo.FilterContact(item):
                    # enforce privacy
                    if self.AllowedToAccess(item, jabberID):
                        contactList.append(item)
        
        return contactList

    # handle errors - just pass it down the the wxViewer
    def HandleErrorResponse(self, jabberID, url, errorMessage):
        viewer = app.association[id(self)]
        viewer.HandleErrorResponse(jabberID, url, errorMessage)
 
    # handle presence changed notification
    def PresenceChanged(self, who):
        myID = id(self)
        if app.association.has_key(myID):
            viewer = app.association[myID]
            viewer.PresenceChanged(who)

    # iterate through the repository to find a contact with the passed in name
    def FindContactByName(self, targetName):
        repository = Repository()
        for item in repository.thingList:
            if isinstance(item, Contact):
                contactName = item.GetFullName()
                if contactName == targetName:
                    return item
        return None
        
    # add a new contact to the repository; the contact parcel is not
    # necessary active when this is called, so only update if we're the
    # current package.  If the methodType is None, don't add a method
    def AddContactWithMethod(self, fullname, methodType, methodLabel, methodValue):
        # first, see if we already have a contact with this name
        newContact = self.FindContactByName(fullname)
        if newContact == None:
            newContact = Contact('Person')      
            newContact.SetNameAttribute(chandler.fullname, fullname)

            # add the contact and commit the changes
            repository = Repository()
            repository.AddThing(newContact)

        if methodType != None and not newContact.HasContactMethod(methodType, methodValue):
            newContactMethod = newContact.AddAddress(methodType, methodLabel)
            attributes = newContactMethod.GetAddressAttributes()
            newContactMethod.SetAttribute(attributes[0], methodValue)
            repository = Repository()
            repository.Commit()
        
        # update only if we're the current package
        if app.wxMainFrame.activeParcel == self:
            self.UpdateFromRepository()

    # find the viewInfo with the passed in title
    def FindViewInfo(self, viewName):
        for viewInfo in self.views:
            if viewInfo.GetTitle().lower() == viewName.lower():
                return viewInfo
        
        # if we didn't find any, return None
        return None

    # remove the passed in view, which might be the current one (or might not)
    def RemoveView(self, viewName):
        viewInfo = self.FindViewInfo(viewName)
        if viewInfo == None:
            return
 
        # remove it from the view list - it must be in the list,
        # since FindViewInfo just got it from there
        index = self.views.index(viewInfo)
        del self.views[index]
        
        # remove it from the sidebar
        url = self.displayName + '/' + viewName
        app.model.URLTree.RemoveURL(url)
        
        # if we're removing the current view, go to the next one
        # the view might not be instantiated, so be careful when checking the viewer
        parcelViewerKey = id(self)
        if app.association.has_key(parcelViewerKey):
            viewer = app.association[parcelViewerKey]

            if viewInfo == viewer.currentViewInfo:
                if index < len(self.views):
                    newViewInfo = self.views[index]
                else:
                    newViewInfo = self.views[-1]
                newViewName = newViewInfo.GetTitle()
                url = self.displayName + '/' + newViewName
                app.wxMainFrame.GoToURL(url)
            
        
        
class wxContactsViewer(wxViewerParcel):   
    # set up the contents of the window  
    def OnInit(self):
        # establish a base ID for widgets
        self.commandID = 100
        self.contactMenu = None
        
        self.remoteAddress = None
        self.lastRemoteAddress = None
        self.remoteLoadInProgress = false
        self.lastChangedTime = 0
        
        # set up the query info
        self.currentViewInfo = self.model.views[self.model.currentViewIndex]

        # allocate the contacts dictionary
        self.contactMetaData = ContactMetaData(self, self.model.path)
        self.contactList = self.QueryContacts()
                
        # allocate the test object that generates fake contacts for testing
        self.contactsTests = ContactsTest(self)
        
        # get the initially selected contact
        if len(self.contactList) > 0:
            self.selectedContact = self.contactList[0]
        else:
            self.selectedContact = None
            
        # hook up the menu items
        EVT_MENU(self, XRCID("NewContactMenuItem"), self.AddNewContactDialog)
        EVT_MENU(self, XRCID("DeleteContactMenuItem"), self.DeleteContactCommand)
        EVT_MENU(self, XRCID("NewAddressMenuItem"), self.AddNewAddress)
        EVT_MENU(self, XRCID("AttributesMenuItem"), self.ShowAttributesDialog)
        EVT_MENU(self, XRCID("TemplatesMenuItem"), self.EditTemplates)
        EVT_MENU(self, XRCID("GenerateContacts"),  self.GenerateContacts)
        EVT_MENU(self, XRCID("ChangeImageMenuItem"), self.ChangeContactImage)
        EVT_MENU(self, XRCID("AddViewMenuItem"), self.AddNewViewCommand)
        EVT_MENU(self, XRCID("EditViewMenuItem"), self.EditViewCommand)
        EVT_MENU(self, XRCID("DeleteViewMenuItem"), self.DeleteViewCommand)
        EVT_MENU(self, XRCID("AboutContactsMenuItem"), self.AboutContactsCommand)
 
        EVT_MENU(self, wxID_CLEAR, self.DeleteContactCommand)
 
        # initialize an image cache for the subviews to use
        self.images = OSAF.contacts.ImageCache.ImageCache(self.model.path)
        
        # create the splitter window
        self.splitter = wxSplitterWindow(self, -1, style=wxSP_NOBORDER)
        self.splitter.SetMinimumPaneSize(128)

        # create the subcomponents      
        self.indexView = ContactsIndexView(self.splitter, self)
        self.contentView = ContactContentView(self.splitter, self, self.indexView, self.selectedContact)      
        self.controlBar = ContactsControlBar(self, self.indexView, self.contentView, self.images)
        self.splitter.SplitHorizontally(self.indexView, self.contentView)
 
        # add the controlbar and the splitter to the window
        self.container = wxBoxSizer(wxVERTICAL)
         
        self.container.Add(self.controlBar, 0, wxEXPAND)
        self.container.Add(self.splitter, 1, wxEXPAND)
    
        self.SetSizerAndFit(self.container)
    
    # called from model to switch views
    def GoToURL(self, remoteAddress, url):
        self.remoteAddress = remoteAddress
        urlParts = url.split('/')
        self.SelectView(urlParts[-1])
        
    # access properties of the current view
    def GetQueryDescription(self):
        return self.currentViewInfo.GetDescription()

    # get the title of the current view, appending the remote
    # address if appropriate
    def GetViewTitle(self):
        titleStr = self.currentViewInfo.GetTitle()
        if self.IsRemote():
            remoteName = app.jabberClient.GetNameFromID(self.remoteAddress)
            remoteText = _('(from %s)') % (remoteName)
            titleStr = titleStr + ' ' + remoteText
        return titleStr

    # return true if this is currently a remote view
    def IsRemote(self):
        return self.remoteAddress != None
    
    def GetSharingPolicy(self):
        return self.currentViewInfo.GetSharingPolicy()
    
    def SetSharingPolicy(self, newPolicy):
        oldPolicy = self.currentViewInfo.GetSharingPolicy()
        if newPolicy != oldPolicy:
            self.currentViewInfo.SetSharingPolicy(newPolicy)
            viewName = 'Contacts/' + self.currentViewInfo.GetTitle()
            app.jabberClient.PermissionsChanged(viewName)
            
    # Override ReplaceViewParcelMenu to set up the parcel menu,
    # append the available views to it, and enable the items properly
    def ReplaceViewParcelMenu(self):    
        self.contactsMenu = wxViewerParcel.ReplaceViewParcelMenu(self)
        self.AddViewMenuItems()
        self.EnableMenuItems()
        
    # add menu items corresponding to the available views
    def AddViewMenuItems(self):
        self.contactsMenu.AppendSeparator()
        currentTitle = self.currentViewInfo.GetTitle()
        
        # bump IDs to avoid conflict
        # FIXME: why do we have to do this?
        self.commandID += 10
        self.viewCommandBase = self.commandID
        
        for viewInfo in self.model.views:
            viewName = viewInfo.GetTitle()
            self.contactsMenu.Append(self.commandID, viewName, viewName, wxITEM_RADIO)
            if viewName == currentTitle:
                self.contactsMenu.Check(self.commandID, true)
            
            handler = SwitchViewHandler(self, viewName)
            wx.EVT_MENU(self, self.commandID, handler.SwitchView) 
            self.commandID += 1
                    
    # enable or disable the contact menu items depending on the item count
    def EnableMenuItems(self):
        hasItems = self.GetContactsCount() > 0
        self.contactsMenu.Enable(XRCID("DeleteContactMenuItem"), hasItems)
        self.contactsMenu.Enable(XRCID("NewAddressMenuItem"), hasItems)
        self.contactsMenu.Enable(XRCID("AttributesMenuItem"), hasItems)
        self.contactsMenu.Enable(XRCID("TemplatesMenuItem"), hasItems)
        self.contactsMenu.Enable(XRCID("ChangeImageMenuItem"), hasItems)

    # helper routine to search the view list for a remote view
    def FindRemoteView(self):
        for viewInfo in self.model.views:
            if viewInfo.IsRemote():
                return viewInfo
        return None
    
    # select the view with the passed-in name
    def SelectView(self, viewName):
        newViewInfo = self.model.FindViewInfo(viewName)
        repositoryChanged = self.lastRemoteAddress != self.remoteAddress
        
        # if it's remote, and not present, make a transient remote view to host it
        if self.remoteAddress != None and newViewInfo == None:
            # see if there's a view info already in the list
            # if so, use it, if not, add one
            remoteMessage = _("This is a remote view")
            newViewInfo = self.FindRemoteView()
            
            if newViewInfo == None:
                newViewInfo = ContactViewInfo(chandler.Contact, None, viewName, remoteMessage)
                newViewInfo.SetRemote(true)
                self.model.views.append(newViewInfo)
            else:
                newViewInfo.SetTitle(viewName)
                newViewInfo.SetDescription(remoteMessage)
                
            # use repository changed to force using it, even if the previous one was also
            # the same remote view object
            repositoryChanged = true
            
        viewChanged = newViewInfo != None and newViewInfo != self.currentViewInfo
        if repositoryChanged or viewChanged:
            self.currentViewInfo = newViewInfo
            self.model.currentViewIndex = self.model.views.index(newViewInfo)

            # check the appropriate view in the menu
            whichView = self.viewCommandBase + self.model.currentViewIndex
            self.contactsMenu.Check(whichView, true)
            self.UpdateFromRepository()
            
    # UpdateFromRepository executes the query to build the itemlist, and then
    # tells the viewer to update its contents accordingly
    def UpdateFromRepository(self):
        # execute the query and build the contact list
        self.contactList = self.QueryContacts()
        # update the control bar and index view
        self.ContactsChanged()
        # make sure the selected contact is present in the new list
        self.EnsureSelectedItem()
            
    # EnsureSelectedItem is called after switching views to ensure
    # that the currently selected item is still in the list.  If not,
    # select a new item
    def EnsureSelectedItem(self):
        selectedContact = self.contentView.contact
        
        try:
            index = self.contactList.index(selectedContact)
        except ValueError:
            # select the first contact
            if len(self.contactList) > 0:
                selectedContact = self.contactList[0]
                self.SetContact(selectedContact)
        
    # we do this to resize the control bar properly after it's opened or closed
    # FIXME: there's probably a better way to do this
    def RelayoutControlBar(self):
        self.container.Remove(self.controlBar)
        self.container.Remove(self.splitter)
        
        self.container.Add(self.controlBar, 0, wxEXPAND)
        self.container.Add(self.splitter, 1, wxEXPAND)
        self.Layout()
        
    def GetAttributeDictionary(self):
        return self.contactMetaData
    
    def SetContact(self, newContact):
        self.contentView.SetContact(newContact)
 
    def SetContactList(self, contactList):
        self.contentView.SetContactList(contactList)
        
    def ContactsChanged(self):
        self.lastChangedTime = time.time()
        
        self.indexView.ContactsChanged()
        self.controlBar.ContactsChanged()
        self.contentView.ContactsChanged()

    # sort function to sort contacts by their sortname
    def SortByName(self, firstContact, secondContact):
        return cmp(firstContact.GetSortName(), secondContact.GetSortName())

    def GetSortedContacts(self):
        return self.contactList
    
    # return a list of contacts that are specified by the current query
    def QueryContacts(self):
        contactList = []
        if self.remoteAddress != None:
            url = self.currentViewInfo.GetURL()
            if app.jabberClient.RequestRemoteObjects(self.remoteAddress, url):
                self.remoteLoadInProgress = true
            else:
                self.remoteLoadInProgress = false
                message = _("Sorry, but %s is not present!") % (self.remoteAddress)
                wxMessageBox(message)
        else:
            repository = Repository()
            for item in repository.thingList:
                if self.currentViewInfo.FilterContact(item):
                    contactList.append(item)
            
            self.remoteLoadInProgress = false
            contactList.sort(self.SortByName)
        
        self.lastRemoteAddress = self.remoteAddress
        return contactList

    # handle errors - terminate loading and put up a message
    def HandleErrorResponse(self, jabberID, url, errorMessage):
        self.remoteLoadInProgress = false
        self.ContactsChanged()
        wxMessageBox(errorMessage)
     
    # add the objects in the passed-in list to the objectlist,
    # and display them.  
    def AddObjectsToView(self, url, objectList, lastFlag):
        # first parsel the url and make sure it's consistent with
        # the view that we're at         
        urlParts = url.split('/')
        viewInfo = self.model.FindViewInfo(urlParts[-1])
        if viewInfo != self.currentViewInfo:
            # FIME: should indicate error somehow, if only to log
            return
        
        for contact in objectList:
            self.contactList.append(contact)
        
        if lastFlag:
            self.remoteLoadInProgress = false
        
        elapsedTime = time.time() - self.lastChangedTime
        if elapsedTime > 1.0 or lastFlag:
            self.SortContacts()
            self.ContactsChanged()
        
    def SortContacts(self):
        self.contactList.sort(self.SortByName)
        return self.contactList

    def AddContact(self, newContact):
        self.contactList.append(newContact)
        return self.SortContacts()
        
    def GetContactsCount(self):
        if self.contactList == None:
            return 0
        return len(self.contactList)
 
    # delete a contact from the database
    def DeleteContact(self, contactToDelete):
        # remove the contact from the contactList
        try:
            index = self.contactList.index(contactToDelete)
            del self.contactList[index]
        except:
            pass

        # remove the contact from the repository
        repository = Repository()
        repository.DeleteThing(contactToDelete)
   
    # here's the code to add a new contact using the passed-in template description
    # FIXME: for now, we only handle the person and company types
    def AddNewContact(self, contactType):   
        template = self.contactMetaData.GetTemplate(contactType)
        classType = template.GetContactClass()
        newContact = Contact(classType)     
        
        # fetch the default name and set it up
        firstDefault = self.contactMetaData.GetNameAttributeDefaultValue(chandler.firstname)
        lastDefault  = self.contactMetaData.GetNameAttributeDefaultValue(chandler.lastname)
        
        if classType == 'Person':
            newContact.SetNameAttribute(chandler.firstname, firstDefault)
            newContact.SetNameAttribute(chandler.lastname, lastDefault)
        else:
            newContact.SetNameAttribute(chandler.fullname, _('New Company'))
            
        # add the new contact to the list
        self.AddContact(newContact)
        self.contentView.SetContact(newContact)
        
        # assign groups, as specified by the template
        groups = template.GetGroups()
        for group in groups:
            newContact.AddGroup(group)
        
        # add the contact method from the template
        addressList = self.contentView.GetAddressList()
        contactMethods = template.GetContactMethods()
        for contactMethod in contactMethods:
            addressList.AddNewAddress(contactMethod, false)
 
        # set up the header and body attributes to display
        attributes = template.GetHeaderAttributes()
        newContact.SetHeaderAttributes(attributes)
        
        attributes = template.GetBodyAttributes()
        newContact.SetBodyAttributes(attributes)

        # commit the object to the repository
        repository = Repository()
        repository.AddThing(newContact)

        # FIXME: hack to force proper layout
        self.contentView.SetContact(None)
        self.contentView.SetContact(newContact)
         
        # start editing the name
        if self.model.useOneNameField:
            attribute = chandler.fullname
        else:
            attribute = chandler.firstname
        
        namePlate = self.contentView.GetNamePlate()
        namePlate.SetEditAttribute(attribute, false)

        self.ContactsChanged()
        self.indexView.SetSelectedContact(newContact)
        self.indexView.Layout()
        self.EnableMenuItems()

    # show a dialog explaining that remote objects can't be edited yey
    def ShowCantEditDialog(self, contact):
        message = _("Sorry, but you don't have permission to edit a remote item.  Would you like to copy it to your local repository?")
        dialog = wxMessageDialog(app.wxMainFrame, message, _("Can't Edit Remote Item"), wxYES_NO | wxICON_QUESTION)
        result = dialog.ShowModal()
        
        # turn the item into a local item by zeroing the remote address and adding it
        # to the repository
        if result == wxID_YES:
            contact.remoteAddress = None
            repository = Repository()
            repository.AddThing(contact)
        
    # menu command handlers       
    
    # delete the selected contact by telling the index view about it
    def DeleteContactCommand(self, event):
        success = self.indexView.DeleteContact()
        if success:
            repository = Repository()
            repository.Commit()
 
            self.EnableMenuItems()
            
    # handle the add new contact command by putting up a dialog to choose the type
    def AddNewContactDialog(self, event):
        if self.remoteAddress != None:
            wxMessageBox(_("Sorry, but you can't add a contact to a remote repository!"))
            return
        
        choiceList = self.contactMetaData.GetTemplateNames()
        choiceList.sort()

        title = _("Add a New Contact:")
        label = _("Select the type of contact to add:")
        lastType = self.model.lastContactType
        dialog = ContactChoiceDialog(app.wxMainFrame, title, label, _("Contact type:"), choiceList, lastType)

        result = dialog.ShowModal()
        if result == wxID_OK:
            contactType = dialog.GetSelection()
            self.AddNewContact(contactType)
            self.model.lastContactType = contactType
         
    # add a new address to the current contact, by telling the content view about it        
    def AddNewAddress(self, event):
        self.contentView.AddNewAddress()

    # tell the content view to show the attributes dialog
    def ShowAttributesDialog(self, event):
        self.contentView.ShowAttributesDialog()
 
    # show a dialog to edit the templates
    def EditTemplates(self, event):
        title = _("Edit Templates")
        label = _("Select a template to change its attributes:")
        addressList = self.contentView.GetAddressList()
        if addressList == None:
            return
        
        dialog = TemplateDialog(app.wxMainFrame, title, label, self, addressList)
        result = dialog.ShowModal()
        if result == wxID_OK:
            dialog.UpdateTemplate()

    # add a new view by bringing up the edit view dialog
    def AddNewViewCommand(self, event):
        title = _("Add a New View:")
        label = _("Create a new view by specifying the properties of the view:")
 
        dialog = EditContactViewDialog(app.wxMainFrame, title, label, self, None)

        result = dialog.ShowModal()
        if result == wxID_OK:
            title, description, sharingPolicy, condition = dialog.GetNewViewInfo()
            
            if title == None or len(title) == 0:
                wxMessageBox(_("Sorry, but a view must have name"))
                return
        
            newViewInfo = self.model.FindViewInfo(title)
            if newViewInfo != None:
                message = _('Sorry, there is already a view named "%s".') % (title)
                wxMessageBox(message)
                return
                
            view = ContactViewInfo(chandler.Contact, condition, title, description)
            view.SetSharingPolicy(sharingPolicy)
            self.model.views.append(view)
            
            # add it to the sidebar, too
            url = self.model.displayName + '/' + title
            app.model.URLTree.AddURL(self, url)

            # tell remote listeners about it
            app.jabberClient.PermissionsChanged(title)

            # finally, go to the new view
            app.wxMainFrame.GoToURL(url, true)
            
   # edit the current ciew by bringing up the edit view dialog
    def EditViewCommand(self, event):
        title = _("Edit the Current View:")
        label = _("Edit the current view by specifying the properties of the view:")

        originalViewInfo = self.currentViewInfo
        originalName = originalViewInfo.GetTitle()
        originalURL = self.model.displayName + '/' + originalViewInfo.GetTitle()
        
        dialog = EditContactViewDialog(app.wxMainFrame, title, label, self, self.currentViewInfo)

        result = dialog.ShowModal()
        if result == wxID_OK:
            
            # user the view info - it might not be the current view info if the user moved somewhere else
            
            viewName, description, sharing, condition = dialog.GetNewViewInfo()
            # set up the info in the current view, and redraw to reflect it
            originalViewInfo.SetTitle(viewName)
            originalViewInfo.SetDescription(description)
            originalViewInfo.SetSharingPolicy(sharing)
 
            url = self.model.displayName + '/' + viewName
            # rename the url
            app.model.URLTree.RenameURL(originalURL, url)
            
            # if we're the current view, redraw the control bar, redo the query and redraw
            if originalViewInfo == self.currentViewInfo:
                self.currentViewInfo = None
                app.wxMainFrame.GoToURL(url)
                
    # delete the current view
    def DeleteViewCommand(self, event):
        viewName = self.currentViewInfo.GetTitle()
        self.model.RemoveView(viewName)

        # tell remote listeners about it
        app.jabberClient.PermissionsChanged(viewName)

    def AboutContactsCommand(self, event):
        pageLocation = pageLocation = self.model.path + os.sep + "AboutContacts.html"
        infoPage = SplashScreen(self, "About Contacts", pageLocation, false)
        if infoPage.ShowModal():
            infoPage.Destroy()

    # command to change the image associated with a contact
    def ChangeContactImage(self, event):
        self.contentView.contentView.GetPhotoImage(event)

    def PresenceChanged(self, who):
        if self.contentView != None:
            self.contentView.PresenceChanged(who)
        
    # command to generate a bunch of fake contacts for testing
    def GenerateContacts(self, event):
        if self.remoteAddress != None:
            wxMessageBox(_("Sorry, but you can't add new contacts to a remote repository!"))
            return
        
        self.contactsTests.GenerateContacts(25)
        self.ContactsChanged()

class SwitchViewHandler:
    def __init__(self, contactsView, viewName):
        self.contactsView = contactsView
        self.viewName = viewName
        
    def SwitchView(self, event):
        url = self.contactsView.model.displayName + '/' + self.viewName
        app.wxMainFrame.GoToURL(url, true)
        
