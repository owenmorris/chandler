__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import string
import time

from application.Application import app
from application.ViewerParcel import *
from application.ChandlerJabber import *
from application.SplashScreen import SplashScreen

from persistence.dict import PersistentDict

from RosterControlBar import RosterControlBar
from RosterMessage import RosterMessage
from RosterDialog import RosterSubscribeDialog

class RosterViewer(ViewerParcel):
    def __init__(self):
        """
          displayName is used to identify the name of the Parcel in the U/I.
        """
        ViewerParcel.__init__(self)
        self.nameToIDMap = PersistentDict()
        self.messageTranscripts = PersistentDict()
        self.pendingMessages = PersistentDict()
        
        tree = app.model.URLTree
        tree.AddURL(self, self.displayName)

        self.SynchronizePresence()
        
    def GoToURL(self, remoteaddress, url):
        self.SynchronizeView()
        
        viewer = app.association[id(self)]
        viewer.GoToURL(url)
        
        return true

    # utility to map a name back to its corresponding ID
    def MapNameToID(self, name):
        if self.nameToIDMap.has_key(name):
            return self.nameToIDMap[name]
        return name
    
    # remap the url to another parcel by stripping off the first part
    def RedirectURL(self, url):
        # translate the colons back to slashes first
        url = url.replace(':', '/')

        urlParts = url.split('/')
        if len(urlParts) > 2:
            urlParts[1] = self.MapNameToID(urlParts[1])
            newURL = string.join(urlParts[1:], '/')
        else:
            newURL = url
        return newURL
    
    def GetURL(self, jabberID):
        """
          return the display url corresponding to the passed in jabberID,
          mapping to the real user's name when possible.
          FIXME: return a presence indicator, which we eventually want
          to be graphical
        """
        jabberName = app.jabberClient.GetNameFromID(jabberID)
        if jabberName == None:
            jabberName = str(jabberID)
            
        #if app.jabberClient.IsPresent(jabberID):
            #jabberName = '* ' + jabberName
        self.nameToIDMap[jabberName] = str(jabberID)
        return self.displayName + '/' + jabberName
        
    def SynchronizePresence(self):
        """
          install the current presence state into the URL tree
        """
        tree = app.model.URLTree
        if app.jabberClient == None:
            return
        if not hasattr(app, 'wxMainFrame'):
            return
                   
        # iterate through the roster, installing any urls that aren't
        # in the tree yet
        urlList = []
        if app.jabberClient.IsConnected():
            rosterList = app.jabberClient.GetRosterIDs(false)
            for jabberID in rosterList:
                url = self.GetURL(jabberID)
                urlList.append(url)
                if not tree.URLExists(url):
                    tree.AddURL(self, url)
            
                # set the color of the link to reflect presence and pending message
                pending = self.HasPendingMessage(jabberID)
                if app.jabberClient.IsPresent(jabberID):
                    if pending:
                        linkColor = wxColour(0, 127, 0)                    
                    else:
                        linkColor = wxColour(0, 0, 0)
                else:
                    if pending:
                        linkColor = wxColour(127, 255, 127)
                    else:
                        linkColor = wxColour(127, 127, 127)
                
                app.wxMainFrame.sideBar.model.SetURLColor(url, linkColor)
            
                # only consider accessible views if client is present
                if app.jabberClient.IsPresent(jabberID) and app.jabberClient.IsChandlerClient(jabberID):
                    viewList = app.jabberClient.GetAccessibleViews(jabberID)
                    if viewList != None:
                        # make a link in the sidebar for each remote view
                        for view in viewList:
                            # since slashes are used by the sidebar to make levels
                            # of the hierarchy, translate it to colon to avoid
                            # making extra levels, which only get in the way
                            mappedView = view.replace('/', ':')
                            subURL = url + '/' + mappedView    
                            urlList.append(subURL)
                            if not tree.URLExists(subURL):
                                tree.AddURL(self, subURL)

        # iterate through all the installed urls, removing any that aren't in
        # the roster using a recursive routine to walk the tree
        self.RemoveSubUrls('Roster', urlList)
    
    # walk the tree recusively, starting at the passed in node,
    # removing any nodes not in the passed-in list
    def RemoveSubUrls(self, urlPath, urlList):
        tree = app.model.URLTree
        installedList = tree.GetURLChildren(urlPath)
        if installedList == None:
            return
        
        for childURL in installedList:
            fullURL = urlPath + '/' + childURL
            self.RemoveSubUrls(fullURL, urlList)
            try:
                index = urlList.index(fullURL)
            except ValueError:
                try:
                    tree.RemoveURL(fullURL)            
                except:
                    print "couldnt remove", fullURL
                    
                
    # respond to presence attributes changing by resyching with the sidebar
    def PresenceChanged(self, who):
        self.SynchronizePresence()
        
        myID = id(self)
        if app.association.has_key(myID):
            viewer = app.association[myID]
            viewer.controlBar.UpdateTitle()
            viewer.EnableMenuItems()
            
    # map the passed-in jabberID to a dictionary key by coercing to a string
    # and removing the resource, if any
    def MapJabberID(self, jabberID):
        idStr = str(jabberID)
        parts = idStr.split('/')
        return parts[0]

    # render the passed-in list of message objects as a text string
    # FIXME: we want to improve this using rich text, but that will come later
    def RenderMessageListAsText(self, messageList):
        messageText = ''
        for message in messageList:
            messageText = messageText + message.RenderShortMessage() + '\n\n'
        return messageText
    
    # return a text rendering of the message transcript corresponding
    # to the passed-in jabberID
    def GetTranscriptText(self, jabberID):
       key = self.MapJabberID(jabberID)
       if self.messageTranscripts.has_key(key):
            messageList = self.messageTranscripts[key]
            return self.RenderMessageListAsText(messageList)
        
       return ''

    # add a message object to a transcript
    def AddToTranscript(self, jabberID, messageObject):
        key = self.MapJabberID(jabberID)
        if self.messageTranscripts.has_key(key):
            messageList = self.messageTranscripts[key]
        else:
            messageList = PersistentList()
            self.messageTranscripts[key] = messageList
            
        messageList.append(messageObject)
        
    # handle receiving a new message by adding it to the appropriate transcript
    def ReceivedMessage(self, fromAddress, subject, body):        
        if fromAddress == None:
            return
        
        currentTime = time.time()
        messageObject = RosterMessage(currentTime, fromAddress, subject, body)
        self.AddToTranscript(fromAddress, messageObject)
        
        # update the transcript view, if there is one
        myID = id(self)
        if app.association.has_key(myID):
            viewer = app.association[myID]
            viewer.UpdateTranscriptView(fromAddress)
        else:
            self.SetPendingMessage(fromAddress, true)

        self.SynchronizePresence()
        
    # manage pending message notification
    def HasPendingMessage(self, jabberID):
        key = self.MapJabberID(jabberID)
        if self.pendingMessages.has_key(key):
            return self.pendingMessages[key]
        return false
    
    def SetPendingMessage(self, jabberID, newState):
        key = self.MapJabberID(jabberID)
        self.pendingMessages[key] = newState
         
class wxRosterViewer(wxViewerParcel):
    def OnInit(self):
        self.commandID = 100
        self.rosterMenu = None
        
        self.url = self.model.displayName
        self.jabberID = None
        
        # allocate the widgets
        panel = wxPanel(self, -1, style=wxSUNKEN_BORDER)
        sizer = wxBoxSizer(wxVERTICAL)
        
        self.transcriptView = wxTextCtrl(panel, -1, '', style=wxTE_MULTILINE | wxTE_READONLY | wxNO_BORDER)
        sizer.Add(self.transcriptView, 1, wxEXPAND)
        
        self.messageEntry = wxTextCtrl(self, self.commandID, '', style=wxTE_PROCESS_ENTER)
        EVT_CHAR(self.messageEntry, self.OnKeystroke)

        self.controlBar = RosterControlBar(self, self)
        
        # add the widgets to the view
        self.container = wxBoxSizer(wxVERTICAL)
        
        self.container.Add(self.controlBar, 0, wxEXPAND)

        label = wxStaticText(self, -1, _("Instant Messaging Transcript:"))
        self.container.Add(label, 0, wxEXPAND | wxALL, 4)

        panel.SetSizerAndFit(sizer)
        self.container.Add(panel, 1, wxEXPAND)
        
        self.entryLabel = wxStaticText(self, -1, _("Type your message here:"))
        self.container.Add(self.entryLabel, 0, wxEXPAND | wxALL, 4)

        self.container.Add(self.messageEntry, 0, wxEXPAND)
        self.container.Add(-1, 4)
        
        self.SetSizerAndFit(self.container)
        
        # hook up the menu items
        EVT_MENU(self, XRCID("AddSubscription"), self.AddSubscription)
        EVT_MENU(self, XRCID("DeleteSubscription"), self.DeleteSubscription)
        EVT_MENU(self, XRCID("ViewAboutRosterPage"), self.ViewAboutRosterPage)

        # update the presence info in the sidebar
        self.model.SynchronizePresence()

    # Override ReplaceViewParcelMenu to set up the parcel menu
    # and enable the items properly
    def ReplaceViewParcelMenu(self):    
        self.rosterMenu = wxViewerParcel.ReplaceViewParcelMenu(self)
        self.EnableMenuItems()

    # enable or disable the contact menu items depending on the item count
    def EnableMenuItems(self):            
        self.rosterMenu.Enable(XRCID("AddSubscription"), true)
        self.rosterMenu.Enable(XRCID("DeleteSubscription"), self.jabberID != None)

    # set the url and update the title bar
    def GoToURL(self, url):
        self.url = url
            
        # set up the jabberID of the correspondent, if any
        urlParts = url.split('/')
        if len(urlParts) > 1:
            self.jabberID = self.model.MapNameToID(urlParts[-1])
        else:
            self.jabberID = None

        self.controlBar.UpdateTitle()
        self.EnableMenuItems()

        # load the message transcript and copy it into the transcript view
        if self.jabberID != None:
            transcriptText = self.model.GetTranscriptText(self.jabberID)
            self.transcriptView.SetValue(transcriptText)
            self.model.SetPendingMessage(self.jabberID, false)
            self.entryLabel.Show()
            self.messageEntry.Show()
            # better synchronizePresence here to reflect pending going away
            self.model.SynchronizePresence()
        else:
            self.transcriptView.Clear()
            self.entryLabel.Hide()
            self.messageEntry.Hide()
             
    # compute the title of the view, based on the url
    def GetViewTitle(self):
        if self.jabberID == None:
            return self.model.displayName
        
        fullJabberID = app.jabberClient.GetCompleteID(self.jabberID)         
        isPresent = app.jabberClient.IsPresent(fullJabberID)
        urlParts = self.url.split('/')
        
        if len(urlParts) <= 1:
            title = self.model.displayName
        else:
            if isPresent:       
                title = _("Messaging with %s") % (urlParts[-1])
            else:
                title = _("%s is not present!") % (urlParts[-1])
 
        return title

    # return the name of the user
    def GetSenderName(self):
        return app.jabberClient.name
    
    # send the contents of the chat field to the original sender
    def SendMessageField(self):
        if self.jabberID != None: 
            messageText = self.messageEntry.GetValue()
            app.jabberClient.SendTextMessage(self.jabberID, messageText)
        
            # also, append the message to the transcript
            message = RosterMessage(None, self.GetSenderName(), '', messageText)
            self.model.AddToTranscript(self.jabberID, message)
            
            transcriptText = self.model.GetTranscriptText(self.jabberID)
            self.transcriptView.SetValue(transcriptText)
        
        # erase the chat field, since the contents were sent
        self.messageEntry.Clear()

    # update the transcript view if necessary
    def UpdateTranscriptView(self, jabberID):
        if self.model.MapJabberID(self.jabberID) == self.model.MapJabberID(jabberID):
            transcriptText = self.model.GetTranscriptText(jabberID)
            self.transcriptView.SetValue(transcriptText)
        else:
            self.model.SetPendingMessage(jabberID, true)
            
    # handle keystrokes in the message entry field    
    def OnKeystroke(self, event):
        keycode = event.GetKeyCode()
        
        # handle return by accepting
        if keycode == 13:
            self.SendMessageField()
        else:
            event.Skip()
    
    # present a dialog box to enter an ID and subscribe to it
    def AddSubscription(self, event):
        dialog = RosterSubscribeDialog(app.wxMainFrame, _("Subscription Info"))

        result = dialog.ShowModal()
        if result == wxID_OK:
            (name, jabberID) = dialog.GetFieldValues()
            # add a contact for this person, if one doesn't already exist
            contactsParcel = app.jabberClient.FindParcel('Contacts')
            if contactsParcel != None:
                contactsParcel.AddContactWithMethod(name, 'jabberID', 'Jabber ID', jabberID)
            
            app.jabberClient.RequestSubscription(jabberID, true)
    
    # delete the subscription of the current entry
    def DeleteSubscription(self, event):
        app.jabberClient.RequestSubscription(self.jabberID, false)
        
    # display the roster about page
    def ViewAboutRosterPage(self, event):
        pageLocation = self.model.path + os.sep + "AboutRoster.html"
        infoPage = SplashScreen(self, _("About Roster"), pageLocation, false)
        if infoPage.ShowModal():
            infoPage.Destroy()
               
    