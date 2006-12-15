#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from bz2 import compress, decompress
from base64 import b64decode
from xml.etree.ElementTree import ElementTree, TreeBuilder
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Encoders import encode_base64
from email import message_from_string
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.mail.imap4 import \
    IMAP4Client, CramMD5ClientAuthenticator, LOGINAuthenticator, \
    NoSupportedAuthentication, MessageSet, Query, Not
from cStringIO import StringIO

from application import schema
from chandlerdb.item.c import CItem
from chandlerdb.util.c import UUID
from repository.item.Access import ACL, ACE, Permissions
from osaf import pim
from osaf.sharing.formats import ElementTreeDOM
from osaf.framework.certstore import ssl
from osaf.mail import smtp

from p2p.account import Conduit, Account, Share
from p2p.worker import Worker
from p2p.format import CloudXMLDiffFormat


def canonize(id, server):

    if not server:
        if '@' in id:
            id, server = id.rsplit('@', 1)
        else:
            raise ValueError, (id, 'server is unspecified')

    return id, server


class MailAccount(Account):

    smtp = schema.One(inverse=schema.Sequence())
    imap = schema.One(inverse=schema.Sequence())

    def __init__(self, *args, **kwds):

        kwds['protocol'] = 'mail'
        if not kwds.get('userid'):
            kwds['userid'] = kwds['imap'].username
        if not kwds.get('server'):
            kwds['server'] = kwds['imap'].host
        super(MailAccount, self).__init__(*args, **kwds)

    def isLoggedIn(self):

        return self.client is not None

    def login(self, printf, autoLogin=False):

        client = self.client

        if client is None:
            repository = self.itsView.repository
            repoId, x, x = repository.getSchemaInfo()
            self.client = client = MailClient(repoId, self, printf)
            worker = MailWorker(repository)
            worker.start(client)

    def send(self, name, peerId):

        if not self.isLoggedIn():
            raise ValueError, "no mail client"

        view = self.itsView
        sidebar = schema.ns('osaf.app', view).sidebarCollection

        version = 0
        repoId = None
        uuid = None

        for collection in sidebar:
            if collection.displayName == name:
                for share in collection.shares:
                    conduit = share.conduit
                    if isinstance(conduit, MailConduit):
                        if conduit.peerId == peerId:
                            version = share.remoteVersion
                            repoId = share.repoId
                            uuid = collection.itsUUID
                            break
                if version:
                    break

        self.client.send(peerId, repoId, name, uuid, version)

    def check(self, peerId):
        
        if not self.isLoggedIn():
            raise ValueError, "no mail client"

        self.client.check(peerId, None, None, None, 0)


class MailClient(object):

    def __init__(self, repoId, account, printf):

        self._repoId = repoId
        self.account = account.itsUUID
        self.printf = printf

    def output(self, string):

        if string is None: # to clear
            string = ''
        else:
            string = "mail: %s" %(string)

        if self.printf is not None:
            self.printf(string)
        else:
            print string

    def send(self, peerId, repoId, name, uuid, version):

        self.worker.queueRequest(('send', (self._repoId, repoId,
                                           name, uuid, version, peerId)))

    def check(self, peerId, repoId, name, uuid, version):

        self.worker.queueRequest(('check', (self._repoId, repoId,
                                            name, uuid, version, peerId)))

    def sendMail(self, view, message):

        account = view[self.account].smtp

        authRequired = account.useAuth
        heloFallback = not authRequired
        securityRequired = account.connectionSecurity == 'TLS'

        if authRequired:
            username = account.username
            password = account.password
        else:
            username = None
            password = None

        retries = account.numRetries
        timeout = account.timeout

        deferred = Deferred()
        deferred.addCallback(self._sendSuccess)
        deferred.addErrback(self._sendFailure)

        # the code below comes from osaf.mail.smtp
        factory = ESMTPSenderFactory(username, password, message['From'],
                                     message['To'], StringIO(str(message)),
                                     deferred, retries, timeout,
                                     1, heloFallback, authRequired,
                                     securityRequired)
        factory.protocol = smtp._TwistedESMTPSender
        factory.testing = False

        if account.connectionSecurity == 'SSL':
            reactor.callFromThread(ssl.connectSSL, account.host, account.port,
                                   factory, view)
        else:
            reactor.callFromThread(ssl.connectTCP, account.host, account.port,
                                   factory, view)

    def _sendSuccess(self, result):

        self.output('mail sent: %s' %(str(result)))

    def _sendFailure(self, exception):

        self.output('error sending mail: %s' %(exception))

    def checkMail(self, view, fromAddress):

        account = view[self.account].imap
        useTLS = account.connectionSecurity == 'TLS'
        username = account.username
        password = account.password

        if isinstance(username, unicode):
            username = username.encode('utf-8')
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        if isinstance(fromAddress, unicode):
            fromAddress = fromAddress.encode('utf-8')

        class _protocol(IMAP4Client):
            MAX_LENGTH = 1048576  # max line length,
                                  # make large enough for search results
            def __init__(_self, *args):
                IMAP4Client.__init__(_self, *args)
                cram = CramMD5ClientAuthenticator(username)
                login = LOGINAuthenticator(username)
                _self.registerAuthenticator(cram)
                _self.registerAuthenticator(login)

            def serverGreeting(_self, capabilities):
                if useTLS:
                    context = _self.transport.contextFactory.getContext()
                    d = _self.startTLS(context)
                    d = d.addCallback(_self.authenticate, password)
                else:
                    d = _self.authenticate(password)
                d = d.addCallback(_self._selectMailbox)
                d = d.addErrback(_self._loginClientInsecure)
                return d.addErrback(_self.catchErrors)

            def _loginClientInsecure(_self, error):
                error.trap(NoSupportedAuthentication)
                d = _self.login(username, password)
                d = d.addCallback(_self._selectMailbox)
                return d.addErrback(_self.catchErrors)

            def _selectMailbox(_self, result):
                self.output("logged into imap")
                d = _self.select("INBOX")
                return d.addCallback(_self._searchMail)

            def _searchMail(_self, result):
                headerQuery = Query(header=('X-chandler', 'p2p'))
                fromQuery = Query(header=('from', fromAddress))
                notDeletedQuery = Not(Query(deleted=True))
                d = _self.search(headerQuery, fromQuery, notDeletedQuery,
                                 uid=True)
                d = d.addCallback(_self._foundMail)
                return d.addErrback(_self.catchErrors)

            def _foundMail(_self, result):
                self.output("imap: found %d messages" %(len(result)))
                if result:
                    _self.messages = messages = MessageSet()
                    for uid in result:
                        messages.add(uid)
                    d = _self.fetchMessage(messages, uid=True)
                    d = d.addCallback(_self._gotMail)
                else:
                    d = _self.logout()
                    d = d.addCallback(_self._done)
                return d.addErrback(_self.catchErrors)

            def _gotMail(_self, result):
                self.output("imap: got mail")
                for data in result.itervalues():
                    message = message_from_string(data['RFC822'])
                    args = (data['UID'], message, fromAddress)
                    self.worker.queueRequest(('receive', args))
#                d = _self.logout()
#                d = d.addCallback(_self._done)
                d = _self.addFlags(_self.messages, ('\\Deleted',), uid=True)
                d = d.addCallback(_self._flagsAdded)
                return d.addErrback(_self.catchErrors)

            def _flagsAdded(_self, result):
                d = _self.logout()
                d = d.addCallback(_self._done)
                return d.addErrback(_self.catchErrors)

            def _done(_self, result):
                #self.output("imap: done")
                pass
                
            def catchErrors(_self, error):
                self.output("error: %s" %(error.getErrorMessage()))

            def lineLengthExceeded(_self, data):
                self.output('line length exceeded')
                return IMAP4Client.lineLengthExceeded(_self, data)

        class _factory(ClientFactory):
            protocol = _protocol
        
        factory = _factory()
        if account.connectionSecurity == 'SSL':
            reactor.callFromThread(ssl.connectSSL, account.host, account.port,
                                   factory, view)
        else:
            reactor.callFromThread(ssl.connectTCP, account.host, account.port,
                                   factory, view)



class MailConduit(Conduit):

    peerId = schema.One(schema.Text)


class MailShare(Share):

    def __init__(self, view, account, repoId, peerId):

        super(MailShare, self).__init__(itsView=view, repoId=repoId)

        self.conduit = MailConduit(itsParent=self, peerId=peerId,
                                   account=account)
        self.format = CloudXMLDiffFormat(itsParent=self)


class MailWorker(Worker):

    shareClass = MailShare

    def __init__(self, repository):

        super(MailWorker, self).__init__('__mail__', repository)

    def findAccount(self, view, peerId):

        userid, server = canonize(peerId, None)

        for account in MailAccount.getKind(view).iterItems():
            if (account.userid == userid and
                account.server == server):
                break
        else:
            account = MailAccount(itsView=view, userid=userid, server=server)
            view.commit()

        return account

    def processRequest(self, view, request):

        op, args = request
        view = self.getView(view)

        if op == 'send':
            view = self._processSend(view, *args)
        elif op == 'check':
            view = self._processCheck(view, *args)
        elif op == 'receive':
            view = self._processReceive(view, *args)
        else:
            raise NotImplementedError, op

        return view

    def _processSend(self, view, fromRepoId, toRepoId, name, uuid, version,
                     toAddress):

        message = self._get_sync(view, fromRepoId, toRepoId,
                                 name, uuid, version, toAddress)
        self.client.sendMail(view, message)
        return view

    def _processCheck(self, view, fromRepoId, toRepoId, name, uuid, version,
                      fromAddress):

        self.client.checkMail(view, fromAddress)
        return view

    def _processReceive(self, view, uid, message, fromAddress):

        self._result_sync(view, uid, message, fromAddress)
        return view

    def _get_sync(self, view, fromRepoId, toRepoId, name, uuid, version, to):

        try:
            view.refresh(None, None, False)

            replyTo = view[self.client.account].imap.replyToAddress.emailAddress

            collection, name, uuid = self.findCollection(view, name, uuid)
            share = self.findShare(view, collection, fromRepoId, replyTo)

            message = MIMEMultipart()
            message['From'] = replyTo
            message['To'] = to
            message['Subject'] = "chandler sent '%s'" %(name)
            message['X-chandler'] = 'p2p'
            textPart = MIMEBase('text', 'plain')
            textPart.set_payload('Chandler sent "%s"' %(name))
            message.attach(textPart)
            attachment = MIMEBase('application', 'octet-stream')

            builder = TreeBuilder()
            dom = ElementTreeDOM()
            data = dom.openElement(builder, 'data')

            keys = set()
            changes = self.computeChanges(view, version, collection, share)
            for key, (_changes, status) in changes.iteritems():
                if key not in keys:
                    attrs = { 'uuid': key.str64() }
                    if status & CItem.DELETED:
                        attrs['status'] = 'deleted'
                        item = dom.openElement(data, 'item', **attrs)
                    else:
                        if key in collection:
                            attrs['status'] = 'member'
                        item = dom.openElement(data, 'item', **attrs)
                        share.format.exportProcess(dom, key, item,
                                                   changes, keys)
                    dom.closeElement(data, 'item')
                elif key in collection:
                    item = dom.openElement(data, 'item', uuid=key.str64(),
                                           status='member')
                    dom.closeElement(data, 'item')

            dom.closeElement(builder, 'data')
            out = StringIO()
            ElementTree(builder.close()).write(out, 'utf-8')
            data = compress(out.getvalue())
            out.close()

            message['X-chandler-p2p-name'] = name
            message['X-chandler-p2p-from'] = fromRepoId.str64()
            if toRepoId is not None:
                message['X-chandler-p2p-to'] = toRepoId.str64()
            message['X-chandler-p2p-item'] = "%s-%d" %(uuid.str64(),
                                                       view.itsVersion)

            attachment.set_payload(data)
            encode_base64(attachment)
            attachment.add_header('Content-Disposition', 'attachment',
                                  name=name)
            message.attach(attachment)
        except:
            view.cancel()
            raise

        share.localVersion = view.itsVersion + 1
        share.established = True
        view.commit()

        return message

    def _result_sync(self, view, uid, message, fromAddress):

        try:
            view.refresh(None, None, False)

            if 'X-chandler-p2p-to' in message:
                toRepoId = UUID(message['X-chandler-p2p-to'])
                if toRepoId != self._repoId:
                    raise RepositoryMismatchError, toRepoId

            repoId = UUID(message['X-chandler-p2p-from'])
            uuid, version = message['X-chandler-p2p-item'].split('-')
            uuid = UUID(uuid)
            version = int(version)
            name = message['X-chandler-p2p-name']
            self.client.output("processing '%s'" %(name))

            collection = view.find(uuid)
            if collection is None:
                collection = pim.SmartCollection(itsView=view, _uuid=uuid,
                                                 displayName=name)
                schema.ns("osaf.app", view).sidebarCollection.add(collection)

                # for now, grant READ to everyone
                acl = ACL()
                acl.append(ACE(schema.ns('p2p', view).all.itsUUID,
                               Permissions.READ))
                collection.setACL(acl, 'p2p')
                isNew = True
            else:
                isNew = False

            share = self.findShare(view, collection, repoId, fromAddress)
            format = share.format

            if isNew:
                share.localVersion = view.itsVersion + 1
            else:
                changes = self.computeChanges(view, share.localVersion,
                                              collection, share)
                if not changes:
                    share.localVersion = view.itsVersion + 1

            payload = message.get_payload(1).get_payload()
            dom = ElementTreeDOM()
            input = StringIO(decompress(b64decode(payload)))
            data = ElementTree(file=input).getroot()
            input.close()

            share.remoteVersion = version
            view.deferDelete()

            for itemElement in dom.iterElements(data):
                attributes = dom.getAttributes(itemElement)
                status = attributes.get('status')
                if status == 'deleted':
                    item = view.findUUID(attributes['uuid'])
                    if item is not None:
                        item.delete()
                else:
                    child = dom.getFirstChildElement(itemElement)
                    if child is not None:
                        item = format.importProcess(dom, child)
                    else:
                        item = view.findUUID(attributes['uuid'])

                    if status == 'member':
                        collection.inclusions.add(item)

            # Kludge until masterEvents filter patch on bug 6970 is checked in
            for item in collection.inclusions:
                if pim.has_stamp(item, pim.EventStamp):
                    event = pim.EventStamp(item)
                    if event.rruleset is not None:
                        event.getMaster().getFirstOccurrence()

        except:
            view.cancel()
            raise

        share.established = True
        view.commit()
        self.client.output("'%s' synchronized" %(collection.displayName))
