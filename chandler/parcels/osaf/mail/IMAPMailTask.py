__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import osaf.framework.tasks.Action as Action
import osaf.contentmodel.mail.Mail as Mail
import repository.item.Query as Query 
import twisted.internet.defer as defer
import twisted.internet.reactor as reactor
import twisted.internet.protocol as protocol
import twisted.protocols.imap4 as imap4
import osaf.framework.twisted.RepositoryViewBase as RepositoryViewBase
import mx.DateTime as DateTime
import email as email
import email.Utils as Utils
import logging as logging



class MailDownloadAction(Action.Action): 

    # In Thread
    def Execute(self, task):

        accountKind = Mail.MailParcel.getEmailAccountKind()
        printed = False 

        for account in Query.KindQuery().run([accountKind]):
            if account.accountType != 'IMAP4':
                str =  "WARNING: Only IMAP Accounts are currently supported. "
                str1 = "%s of type %s will be ignored" % (account.displayName, account.accountType)
                logging.error(str, str1)
                continue
            
            if not printed:
                logging.info("IMAP MAIL TASK CHECKING FOR NEW MAIL")
                printed = True
               
            viewName = "%s_%s" % (account.displayName, account.itsUUID)
            
            IMAPDownloader(account.itsUUID, viewName).getMail()        
        

class ChandlerIMAP4Client(imap4.IMAP4Client):
    
    def serverGreeting(self, caps):

        self.serverCapabilities =  self.__disableTLS(caps)

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
        logging.error("Unable to connect to server ", reason)

    
        
class IMAPDownloader(RepositoryViewBase.RepositoryViewBase):
    
    # In Thread
    def __init__(self, accountUUID, viewName):    
        
        super(IMAPDownloader, self).__init__(viewName)
        
        self.proto = None
        self.accountUUID = accountUUID
        self.account = None
        self.downloadedStr = None
                 
         
    # In Thread
    def getMail(self):
        if __debug__:
            self.printCurrentView("getMail")
                
        reactor.callFromThread(self.__getMail)  
       
    # In Twisted
    def __getMail(self):
        """If in the thread of execution and not the Twisted Reactor 
           thread one must manually reset the view to the previous view.
           Other classes using that thread will assume one view per thread 
           and will try repository operations on the wrong view"""
        self.setViewCurrent()
        
        try:
            if __debug__: 
                self.printCurrentView("__getMail")
                
            self.account = self.getAccount()
            self.account.setPinned()
             
            serverName = self.account.serverName
            serverPort = self.account.serverPort
                    
            if __debug__: 
                self.printAccount()
        
        finally:
            self.restorePreviousView()
        
        factory = ChandlerIMAP4Factory(self.loginClient, self.catchErrors)
        reactor.connectTCP(serverName, serverPort, factory)     
 
    # In Twisted Reactor or in Thread
    def printAccount(self):
        self.printCurrentView("printAccount")
        
        str  = "\nHost: %s\n" % self.account.serverName
        str += "Port: %d\n" % self.account.serverPort
        str += "Username: %s\n" % self.account.accountName
        str += "Password: %s\n" % self.account.password
        
        self.log.info(str)

    # In Twisted Reactor
    def catchErrors(self, result):
        self.log.error("Twisted Error %s" % result)
   
    # In Twisted Reactor
    def loginClient(self, result, proto):

        self.setViewCurrent()  
       
        try:       
            if __debug__: 
                self.printCurrentView("loginClient")  
                
            """ Save the IMAP4Client instance """
            self.proto = proto

            """ Login using plain text login """

            return self.proto.login(str(self.account.accountName), 
                                    str(self.account.password)).addCallback(self.selectInbox)
        finally:
           self.restorePreviousView()

        
    # In Twisted Reactor
    def selectInbox(self, result):
        if __debug__:
            self.printCurrentView("selectInbox ***Could be wrong view***")

        self.printInfo("Checking Inbox for new mail messages")
        
        return self.proto.select("INBOX").addCallback(self.checkForNewMessages)
    
    # In Twisted Reactor
    def checkForNewMessages(self, msgs):   
        
        self.setViewCurrent()   
        
        try:
            if __debug__:
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
        
    # In Twisted Reactor     
    def getMessagesFromUIDS(self, msgs):

        self.setViewCurrent()
        
        try:
            if __debug__:
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
            
    # In Twisted Reactor 
    def disconnect(self, result = None):
        
        if __debug__:
            self.printCurrentView("disconnect")

        self.proto.close()
        self.proto.transport.loseConnection()

    # In Twisted Reactor 
    def fetchMessages(self, msgs):
        
        if __debug__:
            self.printCurrentView("fetchMessages")

        self.setViewCurrent()       
      
        try:
            """ Refresh our view before adding items to our mail account
                and commiting. Will not cause merge conflicts since
                no data changed in view in yet """ 
            self.view.commit()
    
            totalDownloaded = 0  

            for msg in msgs:
                repMessage = make_message(msgs[msg]['RFC822'])
                self.account.downloadedMail.append(repMessage)

                uid = long(msgs[msg]['UID'])
            
                if uid > self.getLastUID():
                    self.setLastUID(uid)
                    totalDownloaded += 1

            self.downloadedStr = "%d messages downloaded to Chandler" % (totalDownloaded)
                      
        finally:
            self.restorePreviousView()
            
        """Commit the view in a Twisted thread to prevent blocking"""  
        self.commitView()
           
            
    def _viewCommitSuccess(self):
        super(IMAPDownloader, self)._viewCommitSuccess()
        
        self.printInfo(self.downloadedStr)
        self.downloadedStr = None

        self.account.setPinned(False)
        
              
    # In Twisted Reactor or in Thread    
    def getLastUID(self):
        return self.account.messageDownloadSequence
    
    # In Twisted Reactor or in Thread
    def setLastUID(self, uid):
        self.account.messageDownloadSequence = uid
        
    # In Twisted Reactor or in Thread        
    def getAccount(self):   
        
        accountKind = Mail.MailParcel.getEmailAccountKind()
        account = accountKind.findUUID(self.accountUUID)
        
        if account is None: 
            self.log.error("No Account for UUID: %s"% self.account.itsUUID)
    
        return account

    # In Twisted Reactor or in Thread        
    def printInfo(self, info):

        if self.account.serverPort != 143:
            str = "[Server: %s:%d User: %s] %s" % (self.account.serverName, 
                                                   self.account.serverPort,  
                                                   self.account.accountName, info)
        else:
            str = "[Server: %s User: %s] %s" % (self.account.serverName, 
                                                self.account.accountName, info)
            
        self.log.info(str)

        
           
def format_addr(addr):
    str = addr[0]
    if str != '':
        str = str + ' '
    str = str + '<' + addr[1] + '>'
    return str
        

def make_message(data):
    msg = email.message_from_string(data)

    m = Mail.MailMessage()
    
    if m is None:
        print "MailMessage was NULL"
        return None
    
    m.dateSent = DateTime.mktime(Utils.parsedate(msg['Date']))
    m.subject = msg['Subject']

    # XXX replyAddress should really be the Reply-to header, not From
    m.replyAddress = Mail.EmailAddressEmailAddress()
    m.replyAddress.emailAddress = format_addr(Utils.parseaddr(msg['From']))
    
    m.toAddress = []
    for addr in Utils.getaddresses(msg.get_all('To', [])):
        ea = Mail.EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.toAddress.append(ea)
    
    m.ccAddress = []
    for addr in Utils.getaddresses(msg.get_all('Cc', [])):
        ea = Mail.EmailAddress()
        ea.emailAddress = format_addr(addr)
        m.ccAddress.append(ea)

    return m
