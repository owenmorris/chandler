__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.tasks.Action import Action
from osaf.contentmodel.mail.Mail import MailParcel, MailMessage, EmailAddress
from repository.item.Query import KindQuery

from twisted.internet import defer, reactor, protocol, error
from twisted.application import internet
from twisted.protocols.imap4 import IMAP4Client 
from twisted.protocols import imap4 
from osaf.framework.twisted.RepositoryViewBase import RepositoryViewBase

import time
import mx.DateTime as DateTime
import email
from email.Utils import parsedate, parseaddr, getaddresses


class MailDownloadAction(Action): 

    #in Thread
    def Execute(self, task):

        accountKind = MailParcel.getEmailAccountKind()
        printed = False 

        for account in KindQuery().run([accountKind]):
            if account.accountType != 'IMAP4':
                print "WARNING: Only IMAP Accounts are currently supported. %s of type %s will be ignored" % (account.displayName, account.accountType)
                continue

            if not printed:
                  print "------------- IMAP MAIL TASK CHECKING FOR NEW MAIL -------------\n"
                  printed = True
               
                
            view = "%s_%d" % (account.displayName, time.time())
            
            IMAPDownloader(account._uuid, view).getMail()        
        

class ChandlerIMAP4Client(IMAP4Client):
    
    def serverGreeting(self, caps):

        ## Uncomment when SSL support enabled
        #self.serverCapabilities =  self.__disableTLS(caps)

        """This is a great way to utilize the IMAP library without
           Custom coding """
            
        d = defer.Deferred().addCallback(self.factory.callback, self
                           ).addErrback(self.factory.errback)
        
        d.callback(True)
        

    def __disableTLS(self, caps):
        """Disables SSL support for debugging so
           a tcpflow trace can be done on the Client / Server
           command exchange"""

        if caps != None:
             try:
                del caps["STARTTLS"]

             except KeyError:
                pass

        return caps
    
    
class ChandlerIMAP4Factory(protocol.ClientFactory):
    protocol = ChandlerIMAP4Client

    def __init__(self, callback, errback):
        self.callback = callback
        self.errback = errback
    
    def buildProtocol(self, addr):
        p = self.protocol()
        p.factory = self
        return p
       
    def clientConnectionFailed(self, connector, reason):  
        """If this called then no connection established"""        
        print"[ERROR unable to connect to server]" 

    
        
        
class IMAPDownloader(RepositoryViewBase):
    
    #In Thread
    def __init__(self, uuid, viewName, debug = False):    
        
        RepositoryViewBase.__init__(self, viewName)
        
        self.proto = None
        self.uuid = uuid
        self.account = None
        self.debug = debug
                 
         
    #In Thread
    def getMail(self):
        if self.debug:
            self.printCurrentView("getMail")
                   
        """Set the appropriate view"""
        self.execInView(self.__getMailInView)
        
        if self.debug: 
            self.printCurrentView("getMail after Exec")
       
    #In Thread
    def __getMailInView(self):
        """If in the thread of execution and not the Twisted Reactor 
           thread one must manually reset the view to the previous view.
           Other classes using that thread will assume one view per thread 
           and will try repository operations on the wrong view"""
        
        if self.debug: 
            self.printCurrentView("__getMailView")
 
        """We are in the current thread here and not the Reactor so we need 
           to set the view before storing the account. 
           The account will be accessed from another 
           thread. Basic example of multiple threads sharing a view"""
        
        self.account = self.getAccount()
        
        """Prevents account from being stale"""
        self.account.setPinned()
        
        if self.debug: 
            self.printAccount()
        
        factory = ChandlerIMAP4Factory(self.loginClient, self.catchErrors)

        """Start the Reactor call chain"""
        reactor.callFromThread(reactor.connectTCP, self.account.serverName, self.account.serverPort, factory)
  

    #in Twisted Reactor or in Thread
    def printAccount(self):
        self.printCurrentView("printAccount")
        print "Host: ", self.account.serverName
        print "Port: ", self.account.serverPort
        print "Username: ", self.account.accountName
        print "Password: ", self.account.password

    #in Twisted Reactor
    def catchErrors(self, result):
        print "ERROR: ", result
   
    #in Twisted Reactor
    def loginClient(self, result, proto):

        self.setViewCurrent()  
       
        try:       
            if self.debug: 
                self.printCurrentView("loginClient")  
            
            """ Save the IMAP4Client instance """
            self.proto = proto

            """ Login using plain text login """

            return self.proto.login(self.account.accountName, 
                                    self.account.password).addCallback(self.selectInbox)
        finally:
           self.restorePreviousView()

    #in Twisted Reactor
    def selectInbox(self, result):
        if self.debug:
            self.printCurrentView("selectInbox ***Could be wrong view***")

        self.printInfo("Checking Inbox for new mail messages")
        return self.proto.select("INBOX").addCallback(self.checkForNewMessages)
    
    #in Twisted Reactor
    def checkForNewMessages(self, msgs):
        
        self.setViewCurrent()   
        
        try:
            if self.debug:
                self.printCurrentView("checkForNewMessages")
        
            exists = msgs['EXISTS']
        
            if exists != 0:
                """ Fetch everything newer than the last UID we saw. """
            
                if self.getLastUID() == 0:                  
                    msgSet = imap4.MessageSet(1, None)       
                else: 
                    msgSet = imap4.MessageSet(self.getLastUID(), None)     

                d = self.proto.fetchUID(msgSet, uid=True) 
                d.addCallback(self.getMessagesFromUIDS)     
            
                return d
        
            self.printInfo("No messages present to download")
            
        finally:
            self.restorePreviousView()
        
    #in Twisted Reactor     
    def getMessagesFromUIDS(self, msgs):

        self.setViewCurrent()
        
        try:
            if self.debug:
                self.printCurrentView("getMessagesFromUIDS")
        
            v = [int(v['UID']) for v in msgs.itervalues()]
            low = min(v)
            high = max(v)

            if high <= self.getLastUID():
                self.printInfo("No new messages found")
            
            else:
                if self.getLastUID() == 0:
                    msgSet = imap4.MessageSet(low, high)
                else:
                    msgSet = imap4.MessageSet(max(low, self.getLastUID() + 1), high)
                
                d = self.proto.fetchMessage(msgSet, uid=True)
                d.addCallback(self.fetchMessages).addCallback(self.disconnect)
                
        finally:
            self.restorePreviousView()
            
    #in Twisted Reactor 
    def disconnect(self, result = None):
        if self.debug:
            self.printCurrentView("disconnect")

        self.proto.close()
        self.proto.transport.loseConnection()

    #in Twisted Reactor 
    def fetchMessages(self, msgs):
 
        self.setViewCurrent()       
      
        try:
            """ Refresh our view before adding items to our mail account
                and commiting """ 
            self.view.commit()
    
            if self.debug:
                self.printCurrentView("fetchMessages")

            totalDownloaded = 0  

            for msg in msgs:
                repMessage = make_message(msgs[msg]['RFC822'])
                self.account.downloadedMail.append(repMessage)

                uid = long(msgs[msg]['UID'])
            
                if uid > self.getLastUID():
                    self.setLastUID(uid)
                    totalDownloaded += 1

            str = "%d messages downloaded to Chandler" % (totalDownloaded)
            
            self.printInfo(str)      
            """commit when all messages parsed and stored"""  
            self.view.commit()
        
            """Hack to get CPIA Gui to recognize commit"""
            Globals.wxApplication.PostAsyncEvent(MainThreadCommit)
            
        finally:
            self.restorePreviousView()
           
    #in Twisted Reactor or in Thread    
    def getLastUID(self):
        return self.account.messageDownloadSequence
    
    #in Twisted Reactor or in Thread
    def setLastUID(self, uid):
        self.account.messageDownloadSequence = uid
        
    #in Twisted Reactor or in Thread        
    def getAccount(self):   
        
        accountKind = MailParcel.getEmailAccountKind()
        account = accountKind.findUUID(self.uuid)
        
        if account is None: 
            print "ERROR No Account for UUID: ", self.uuid
    
        return account

    #in Twisted Reactor or in Thread        
    def printInfo(self, info):

        if self.account.serverPort != 143:
            str = "[Server: %s:%d User: %s] " % (self.account.serverName, 
                                                 self.account.serverPort,  
                                                 self.account.accountName)
        else:
            str = "[Server: %s User: %s] " % (self.account.serverName, 
                                              self.account.accountName)

        print str, info
           
def format_addr(addr):
    str = addr[0]
    if str != '':
        str = str + ' '
    str = str + '<' + addr[1] + '>'
    return str
        

def make_message(data):
    msg = email.message_from_string(data)

    m = MailMessage()
    
    if m is None:
        print "MailMessage was NULL"
        return None
    
    m.dateSent = DateTime.mktime(parsedate(msg['Date']))
    m.subject = msg['Subject']

    # XXX replyAddress should really be the Reply-to header, not From
    m.replyAddress = EmailAddress()
    m.replyAddress.emailAddress = format_addr(parseaddr(msg['From']))
    
    m.toAddress = []
    for addr in getaddresses(msg.get_all('To', [])):
        ea = EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.toAddress.append(ea)
    
    m.ccAddress = []
    for addr in getaddresses(msg.get_all('Cc', [])):
        ea = EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.ccAddress.append(ea)

    return m


def MainThreadCommit():
    Globals.repository.commit()
