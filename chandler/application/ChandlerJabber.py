#!bin/env python

"""
This package is used to manage presence of other Chandler clients
using Jabber.  It maintains a dictionary of the presence state for
everyone whose presence we have subscribed to.  It's based on work
done for vista but rewritten for Chandler conventions
"""
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"

from wxPython.wx import *

import string
import time
import cPickle
import base64

import xmlstream
from jabber import *

import application.Application

# jabber callbacks
def messageCallback(connection, messageElement):
    connection.jabberclient.HandleMessage(messageElement)
        
def presenceCallback(connection, presenceElement):
    connection.jabberclient.HandlePresence(presenceElement)

def iqCallback(connection, iqElement):
    connection.jabberclient.HandleIq(iqElement)

class PresenceState:
    def __init__(self, who, type, status, resource):
        self.who = who
        self.type = type
        self.status = status
        self.resource = resource
    
class JabberClient:
    def __init__(self, application):
        self.application = application
        
        self.jabberID = None
        self.password = ''
        
        self.connection = None
        self.roster = None
        
        self.connected = false
        self.loggedIn = false
        self.timer = None
        
        self.presenceStateMap = {}
        self.accessibleViews = {}
        self.openPeers = {}
                
        self.ReadAccountFromPreferences()
        self.Login()

    def HasLoginInfo(self):
        self.ReadAccountFromPreferences()
        if self.jabberID == None or len(self.jabberID) < 3:
            return false
        return true

    def IsConnected(self):
        return self.connection != None

    def IsPresent(self, jabberID):		
        presenceState = self.GetPresenceState(jabberID)
        if presenceState == None:
            return false
        return presenceState.type == 'available'
        
    # extract the username from the jabber_id
    def GetUsername(self):
        nameParts = self.jabberID.split('@')
        return nameParts[0]
    
    # extract the servername from the jabber_id
    def GetServername(self):
        nameParts = self.jabberID.split('@')
        serverName = nameParts[1]
        serverNameParts = serverName.split('/')
        return serverNameParts[0]

    # get the account information from the preferences system
    def ReadAccountFromPreferences(self):
        self.jabberID = self.application.model.preferences.GetPreferenceValue('chandler/identity/jabberID')
        self.password = self.application.model.preferences.GetPreferenceValue('chandler/identity/jabberpassword')
        self.name = self.application.model.preferences.GetPreferenceValue('chandler/identity/username')
        self.email = self.application.model.preferences.GetPreferenceValue('chandler/identity/emailaddress')
                                        
    # login to the Jabber server
    def Login(self):
        if self.loggedIn or not self.HasLoginInfo():
            return
        
        username = self.GetUsername()
        servername = self.GetServername()
        
        self.connection = Client(host=servername, debug=0)
        try:
            self.connection.connect()
        except IOError, e:
            print "couldnt connect: %s" % e
            self.connection = None
            return

        # store a reference to the client object in the connection
        self.connection.jabberclient = self
        
        if not self.IsRegistered():     
            if not self.Register():
                self.connection.disconnect()
                print "couldnt register ", self.name
                return
        
        if self.connection.auth(username, self.password, 'Chandler'):	            
            self.connection.setPresenceHandler(presenceCallback)
            self.connection.setMessageHandler(messageCallback)
            self.connection.setIqHandler(iqCallback)
            self.connected = TRUE
    
            self.roster = self.connection.requestRoster()
            self.connection.sendInitPresence()
            self.loggedIn = TRUE		

            # arrange to get called periodically while we're looged in
            self.timer = JabberTimer(self)
            self.timer.Start(400)    
        
            # request the roster to gather initial presence state
            self.roster = self.connection.requestRoster()
            
        else:
            wxMessageBox(_("There is an authentication problem. We can't log into the jabber server.  Perhaps your password is incorrect."))
            self.Logout()

    # return all the status info about a given ID
    def GetPresenceState(self, jabberID):
        key = str(jabberID)
        if self.presenceStateMap.has_key(key):
            return self.presenceStateMap[key]
        return None
   
    def SetPresenceState(self, jabberID, state):
        key = str(jabberID)
        self.presenceStateMap[key] = state
       
    # dump the roster, mainly for debugging
    def DumpRoster(self):
        print "resources ", self.resourceMap
        
        roster = self.connection.requestRoster()
        ids = roster.getJIDs()
        for id in ids:
            name = roster.getName(id)
            online = roster.getOnline(id)
            status = roster.getStatus(id)
            
            isOnline = roster.isOnline(id)
            print id, name, online, status, isOnline

    def IsChandlerClient(self, jabberId):
        basicID = jabberId.getStripped()
        if not self.resourceMap.has_key(basicID):
            return false
        
        resource = self.resourceMap[basicID]
        return string.find(resource, 'Chandler') >= 0
    
    # return a list of all the jabber_ids in the roster, with the
    # active ones first.
    # optionally, filter for Chandler clients only
    def GetRosterIDs(self, chandlerOnly):
        if self.connection == None:
            return []

        #self.roster = self.connection.requestRoster()
        ids = self.roster.getJIDs()
         
        activeIDs = []
        inactiveIDs = []
        
        for id in ids:
             if chandlerOnly:
                if not self.IsChandlerClient(id):
                    continue
                   
             if self.IsPresent(id):
                 activeIDs.append(id)		
             else:
                 inactiveIDs.append(id)
        
        for id in inactiveIDs:
            activeIDs.append(id)
            
        return activeIDs

    # logout from the jabber server and terminate the connection
    def Logout(self):
        if self.connected:
            self.connection.disconnect()
            
        self.connected = false
        self.connection = None
        self.loggedIn = false
        
        # cancel the periodic timer calls
        if self.timer != None:
            self.timer.Stop()
            self.timer = None
    
    # manage the accessible views
    def GetAccessibleViews(self, jabberID):
        strippedID = jabberID.getStripped()
        if self.accessibleViews.has_key(strippedID):
            return self.accessibleViews[strippedID]	

        self.RequestAccessibleViews(strippedID)
        # add empty key to avoid repeated requests
        self.accessibleViews[strippedID] = {}
        return None
        
    def SetAccessibleViews(self, jabberID, newViews):
        strippedID = jabberID.getStripped()
        
        self.accessibleViews[strippedID] = newViews
        self.NotifyPresenceChanged(strippedID)
    
    # the following is invoked when permissions have changed on some view,
    # so we can notify anyone who cares
    def PermissionsChanged(self, view):
        for jabberID in self.openPeers.keys():
            if self.openPeers[jabberID] == 1:
                self.HandleViewRequest(jabberID)
                            
    # handle requests for accessible views 
    def HandleViewRequest(self, requestJabberID):
        # get the dictionary containing the accessible views
        views = self.application.GetAccessibleViews(requestJabberID)
        
        # encode the viewList
        viewStr = self.EncodePythonObject(views)		
                
        # send it back to the requestor		
        self.SendViewResponse(viewStr, requestJabberID, 'chandler:response-views')
        self.openPeers[requestJabberID] = 1
        
    def FixExtraBlanks(self, str):
        result = string.replace(str, ' ', '')
        result = xmlstream.XMLunescape(result)
        #result = string.replace(result, '--b--', ' ')
        return result

    # send a response to a view request back to the initiator
    def SendViewResponse(self, responseStr, responseAddress, requestType):
        responseMessage = Message(responseAddress, responseStr)
        responseMessage.setX(requestType)
        self.connection.send(responseMessage)
        
    # handle responses to requests for accessible views
    def HandleViewResponse(self, fromAddress, responseBody):
        newViews = self.DecodePythonObject(reponseBody)
        self.SetAccessibleViews(fromAddress, newViews)
                        
    # handle an incoming message
    def HandleMessage(self, messageElement):
        type = messageElement.getType()
        body = messageElement.getBody()
        fromAddress = messageElement.getFrom()
        toAddress = messageElement.getTo()
        subject = messageElement.getSubject()
        
        xRequest = messageElement.getX()		
        if xRequest != None:
            if xRequest == 'chandler:request-objects':
                # the url is in the subject
                self.HandleObjectRequest(fromAddress, subject)
                return
            elif xRequest == 'chandler:receive-objects':
                # the url is in the subject
                self.HandleObjectResponse(fromAddress, subject, body, false)
                return
            elif xRequest == 'chandler:receive-objects-done':
                # the url is in the subject
                self.HandleObjectResponse(fromAddress, subject, body, true)
                return
            elif xRequest == 'chandler:receive-error':
                self.HandleErrorResponse(fromAddress, body)
                return
            elif xRequest == 'chandler:request-views':
                self.HandleViewRequest(fromAddress)
                return	
            elif xRequest == 'chandler:response-views':
                self.HandleViewResponse(fromAddress, body)
                return	
        
        # it's a mainstream instant message (not one of our structured ones).
        # FIXME: eventually, invoke our instant messaging client
        message = _("Message from ") + str(fromAddress) + _(" about ") + str(subject) + ". Cant handle yet..."
        wxMessageBox(message)
        
    # handle incoming presence requests by automatically accepting them
    def HandlePresence(self, presenceElement):
        type = presenceElement.getType()
        fromAddress = presenceElement.getFrom()
        who = fromAddress.getStripped()
        status = presenceElement.getStatus()
        
        if type == None:
            type = 'available'
        
        resource = fromAddress.getResource()

        state = PresenceState(who, type, status, resource)
        self.SetPresenceState(who, state)
        
        # invoke a dialog to confirm the subscription request if necessary
        if type == 'subscribe' or type == 'unsubscribe':
            self.ConfirmSubscription(type, who)
        else:
            self.NotifyPresenceChanged(who)
            
    # handle iq requests
    # FIXME: do we need this - we're not really doing anything with it now...
    def HandleIq(self, iqElement):
        type = iqElement.getType()
        fromAddress = iqElement.getFrom()
        query = iqElement.getQuery()
        error = iqElement.getError()
 
    # initiate a request of objects from a remote view
    # pass the desired URL in the subject
    def RequestRemoteObjects(self, jabberID, url):
        messageText = _("Requesting remote objects from ") + url    
        requestMessage = Message(jabberID, messageText)
        requestMessage.setX('chandler:request-objects')
        requestMessage.setSubject(url)
        self.connection.send(requestMessage)

    # send a response from an object request back to the requestor
    def SendObjectResponse(self, jabberID, subject, body, responseType):
        responseMessage = Message(jabberID, body)
        responseMessage.setX(responseType)
        responseMessage.setSubject(subject)
        self.connection.send(responseMessage)
        
    # send a message requesting a list of views that are accessible to this client
    def RequestAccessibleViews(self, jabberID):
        messageText = _('Requesting accessible views')
        requestMessage = Message(jabberID, messageText)
        requestMessage.setX('chandler:request-views')
        requestMessage.setSubject(messageText)
        self.connection.send(requestMessage)
 
    # handle receiving a request for objects from a url 
    # ask the application for the objects, then send them back to the requestor
    def HandleObjectRequest(self, fromAddress, url):
        objectList = self.application.GetViewObjects(url)
    
        # we can send the objects back in ask many responses as we like
        # for simplicity's sake, we'll send them back one at a time at
        # first, and then later tweak for better performance
        resultList = []
        granularity = 3
        for resultObject in objectList:
            resultList.append(resultObject)
            if len(resultList) >= granularity:
                resultString = self.EncodeObjectList(resultList)
                self.SendObjectResponse(fromAddress, url, resultString, 'chandler:receive-objects')
                resultList = []
        
        # send the objects left-over in the list, even if it's empty, so the
        # application knows its the last response
        resultString = self.EncodeObjectList(resultList)
        self.SendObjectResponse(fromAddress, url, resultString, 'chandler:receive-objects-done')
        
    # handle receiving a reponse to an object request.  The lastFlag
    # is true when it's the last response to the request, and the url
    # is the view that should display the objects, which is typically
    # the one that initiated the request
    def HandleObjectResponse(self, fromAddress, url, body, lastFlag):        
        # decode the string from the body of the received message to an objectlist
        objectList = self.DecodeObjectList(body)
        
        # send the objects back to the relevant view
        if len(objectList) > 0:
            self.application.AddObjectsToView(url, objectList)
            
        if lastFlag:
            self.application.ObjectResponseCompleted(url)
            
    # handle receiving notification of an error to an object request
    # FIXME: handle errors soon by telling the application to put up a dialog
    def HandleErrorResponse(self, fromAddress, body):
        pass
    
    # encode a Python object into a text string, using cPickle and base64 encoding
    def EncodePythonObject(self, objectToEncode):
        viewStr = cPickle.dumps(objectToEncode)		
        viewStr = base64.encodestring(viewStr)
        return viewStr
    
    # decode a Python object from a text string, using base64 and cPickle
    def DecodeObjectList(self, objectStr):
        mappedObjectStr = objectStr.encode('ascii')
        mappedObjectStr = self.FixExtraBlanks(mappedObjectStr)
        mappedObjectStr = base64.decodestring(mappedObjectStr)
        return cPickle.loads(mappedObjectStr)	
    
    # put up a dialog to confirm the subscription request
    def ConfirmSubscription(self, subscriptionType, who):
        message = '%s wishes to %s to your presence information.  Do you approve?' % (who, subscriptionType)
        result = tkMessageBox.askquestion('Subscription Request', message)
        
        if result == 'yes':
            if subscriptionType == 'subscribe':
                self.connection.send(Presence(to=who, type='subscribed'))
                self.connection.send(Presence(to=who, type='subscribe'))
            elif subscriptionType == 'unsubscribe':
                self.connection.send(Presence(to=who, type='unsubscribed'))
                self.connection.send(Presence(to=who, type='unsubscribe'))

    # notify the presence panel that presence has changed
    
    def NotifyPresenceChanged(self, who):
        app = application.Application.app
        if app.presenceWindow != None:
            app.presenceWindow.PresenceChanged(who)
        
    # register the user
    def Register(self):
        self.connection.requestRegInfo()
        
        self.connection.setRegInfo('name', self.name)
        self.connection.setRegInfo('password', self.password)
        self.connection.setRegInfo('username', self.GetUsername())
        self.connection.setRegInfo('email', self.email)
        
        registerResult = self.connection.sendRegInfo()
        error = registerResult.getError()
        return error == None
                    
    # return TRUE if we're registered with our server
    def IsRegistered(self):
        username = self.GetUsername()
        
        authGetIQ = Iq(type='get')
        authGetIQ.setID('auth-get')
        q = authGetIQ.setQuery('jabber:iq:auth')
        q.insertTag('username').insertData(username)
        self.connection.send(authGetIQ)
    
        authRetNode = self.connection.waitForResponse("auth-get")
        return authRetNode != None
        
    # given a contact object, request or cancel a subscription to the
    # presence of the associated jabber_id
    def RequestSubscription(self, jabberID, subscribeFlag):
        if jabberID == None:
            tkMessageBox.showerror('No Jabber ID. Please enter a jabber ID before subscribing!')
            return
        
        # first, add or remove the new item to the roster	
        rosterIQ = Iq(type='set')
        query = rosterIQ.setQuery('jabber:iq:roster')
        item = query.insertTag('item')
        item.putAttr('jid', str(jabberID))
            
        if subscribeFlag:
            item.putAttr('subscription', 'none')
        else:
            item.putAttr('subscription', 'remove')
        self.connection.send(rosterIQ)
            
        # then send a presence subscription/unsubscribe request	
        if subscribeFlag:
            subscribeType = 'subscribe'
        else:
            subscribeType = 'unsubscribe'
        self.connection.send(Presence(to=jabberID, type=subscribeType))
        
# here's a subclass of timer to periodically drive the event mechanism
class JabberTimer(wxTimer):
    def __init__(self, jabberClient):
        self.jabberClient = jabberClient
        wxTimer.__init__(self)
        
    def Notify(self):
        if self.jabberClient.connection != None:
            self.jabberClient.connection.process(0)			
        
