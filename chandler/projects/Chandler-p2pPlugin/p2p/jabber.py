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

import traceback

from twisted.words.protocols.jabber import client, jid
from twisted.words.xish import domish
from twisted.internet import reactor

from chandlerdb.item.c import CItem
from chandlerdb.util.c import UUID
from repository.persistence.Repository import RepositoryWorker
from repository.item.Access import AccessDeniedError, ACL, ACE, Permissions

from application import schema
from osaf import pim
from osaf.sharing import formats
from osaf.framework.certstore import ssl

from p2p.account import Account, Conduit, User, Share
from p2p.format import CloudXMLDiffFormat
from p2p.errors import RepositoryMismatchError


def canonize(id, server):

    if '/' in id:
        id, resource = id.split('/', 1)
    else:
        resource = 'chandler'

    if not server:
        if '@' in id:
            id, server = id.rsplit('@', 1)
        else:
            raise ValueError, (id, 'server is unspecified')

    return id, server, resource


def login(view, printf, id, server, password, useSSL):

    id, server, resource = canonize(id, server)

    default = True
    for account in JabberAccount.iterItems(view):
        default = False
        if (account.userid == id and
            account.server == server and
            account.resource == resource):
            break
    else:
        account = JabberAccount(itsView=view, userid=id,
                                server=server, resource=resource,
                                password=password, useSSL=useSSL,
                                default=default, autoLogin=default)
        view.commit()

    account.login(printf)


class JabberAccount(Account):

    server = schema.One(schema.Importable)
    password = schema.One(schema.Text)
    resource = schema.One(schema.Text, initialValue='chandler')

    _clients = {}

    def __init__(self, *args, **kwds):

        kwds['protocol'] = 'jabber'
        super(JabberAccount, self).__init__(*args, **kwds)

    def isLoggedIn(self):

        client = self.client
        return client is not None and client.connected

    def getId(self):

        if '@' in self.userid:
            return "%s/%s" %(self.userid, self.resource)
        else:
            return "%s@%s/%s" %(self.userid, self.server, self.resource)

    def login(self, printf, autoLogin=False):

        client = self.client

        if client is None:
            repository = self.itsView.repository
            repoId, x, x = repository.getSchemaInfo()
            self.client = client = JabberClient(repoId, self, printf)
            server = JabberServer(repository)
            server.start(client)

        reactor.callFromThread(client.connect, self.password,
                               self.useSSL, False, self.itsView)

    def subscribe(self, name, peerId):

        if not self.isLoggedIn():
            raise ValueError, "no connection"

        if '/' not in peerId:
            peerId += "/chandler"

        view = self.itsView
        sidebar = schema.ns('osaf.app', view).sidebarCollection

        version = 0
        repoId = None
        uuid = None

        for collection in sidebar:
            if collection.displayName == name:
                for share in collection.shares:
                    conduit = share.conduit
                    if isinstance(conduit, JabberConduit):
                        if conduit.peerId == peerId:
                            version = share.remoteVersion
                            repoId = share.repoId
                            uuid = collection.itsUUID
                            break
                if version:
                    break

        reactor.callFromThread(self.client.sync,
                               peerId, repoId, name, uuid, version)

    def sync(self, share):

        if not self.isLoggedIn():
            raise ValueError, "no connection"
            
        collection = share.contents
        reactor.callFromThread(self.client.sync,
                               share.conduit.peerId, share.repoId,
                               collection.displayName,
                               collection.itsUUID, share.remoteVersion)

        return None

    def _getClient(self):
        return JabberAccount._clients.get(self.itsUUID)

    def _setClient(self, client):
        JabberAccount._clients[self.itsUUID] = client

    client = property(_getClient, _setClient)


class JabberShare(Share):

    repoId = schema.One(schema.UUID)
    remoteVersion = schema.One(schema.Long)
    localVersion = schema.One(schema.Long)
    collectionName = schema.One(schema.Text)


class JabberConduit(Conduit):

    peerId = schema.One(schema.Text)


class DomishDOM(formats.AbstractDOM):

    def addElement(self, parent, tag, content=None, **attrs):

        element = parent.addElement(tag)

        if content is not None:
            element.children.append(content)
        for key, value in attrs.iteritems():
            element[key] = value

        return element

    def addContent(self, element, content):
        element.children.append(content)

    def setAttribute(self, element, name, value):
        element[name] = value

    def setAttributes(self, element, *pairs, **kwds):
        for key, value in pairs:
            element[key] = value
        for key, value in kwds.iteritems():
            element[key] = value

    def getTag(self, element):
        return element.name

    def getAttribute(self, element, name):
        return element.attributes.get(name)

    def getAttributes(self, element):
        return element.attributes

    def iterElements(self, element):
        return element.elements()

    def getFirstChildElement(self, element):
        return element.firstChildElement()



def subscribe(view, printf, to):

    if jabberClient is None:
        raise ValueError, "no connection"

    reactor.callFromThread(jabberClient.subscribe, to)


def unsubscribe(view, printf, to):

    if jabberClient is None:
        raise ValueError, "no connection"

    reactor.callFromThread(jabberClient.unsubscribe, to)


class JabberClient(object):

    def __init__(self, repoId, account, printf):

        self._repoId = repoId
        self.account = account.itsUUID
        self.host = account.server
        self.id = jid.JID(account.getId())
        self.printf = printf
        self.connected = False

    def output(self, string):

        if string is None: # to clear
            string = ''
        else:
            string = "jabber: %s" %(string)

        if self.printf is not None:
            self.printf(string)
        else:
            print string

    def connect(self, password, useSSL, register, view):

        factory = client.basicClientFactory(self.id, password)
        self.connected = False

        if register:
            invalidUser = lambda x: factory.authenticator.registerAccount()
        else:
            invalidUser = self.invaliduser

        factory.addBootstrap('//event/stream/authd',
                             self.authd)
        factory.addBootstrap("//event/client/basicauth/authfailed",
                             self.authfailed)
        factory.addBootstrap("//event/client/basicauth/invaliduser",
                             invalidUser)
        factory.addBootstrap("//event/stream/error",
                             self.error)

        if useSSL:
            ssl.connectSSL(self.host, 5223, factory, view)
        else:
            reactor.connectTCP(self.host, 5222, factory)

    def authd(self, xmlstream):

        self.output("%s authenticated" %(self.id.full()))

        self.xmlstream = xmlstream
        presence = domish.Element(('jabber:client', 'presence'))
        xmlstream.send(presence)
        
        #xmlstream.addObserver('/message', self.message)
        xmlstream.addObserver('/presence', self.presence)
        xmlstream.addObserver('/iq', self.iq)
        
        self.connected = True

    def sendMessage(self, to, body):
        
        message = domish.Element(('jabber:client', 'message'))
        message['to'] = to
        message['type'] = 'chat'
        
        message.addElement('body', None, body)
        
        self.xmlstream.send(message)

    def subscribe(self, to):

        presence = domish.Element(('jabber:client', 'presence'))
        presence['to'] = to
        presence['type'] = 'subscribe'

        self.xmlstream.send(presence)
        
    def unsubscribe(self, to):

        presence = domish.Element(('jabber:client', 'presence'))
        presence['to'] = to
        presence['type'] = 'unsubscribe'

        self.xmlstream.send(presence)

    def sync(self, to, repoId, name, uuid, version):

        iq = client.IQ(self.xmlstream, "get")
        iq.addElement(("jabber:x:chandler", "query"))
        sync = iq.query.addElement('sync')
        sync['fromRepoId'] = self._repoId.str64()
        if repoId is not None:
            sync['toRepoId'] = repoId.str64()
        sync['name'] = name
        if uuid is not None:
            sync['uuid'] = uuid.str64()
        sync['version'] = str(version)
        iq.send(to)

    def invaliduser(self, elem):
        self.output("INVALIDUSER: %s" %(elem.toXml().encode('utf-8')))

    def authfailed(self, elem):
        self.output("AUTHFAILED: %s" %(elem.toXml().encode('utf-8')))

    def error(self, elem):
        self.output("ERROR: %s" %(elem.toXml().encode('utf-8')))

    def message(self, elem):
        self.output("MESSAGE: %s" %(elem.toXml().encode('utf-8')))

    def presence(self, elem):

        type = elem.attributes.get('type')
        if type == 'subscribe':
            presence = domish.Element(('jabber:client', 'presence'))
            presence['to'] = elem['from']
            presence['type'] = 'subscribed'
            self.xmlstream.send(presence)

        elif type == 'unsubscribe':
            presence = domish.Element(('jabber:client', 'presence'))
            presence['to'] = elem['from']
            presence['type'] = 'unsubscribed'
            self.xmlstream.send(presence)

        else:
            print "PRESENCE: %s" %(elem.toXml().encode('utf-8'))

    def iq(self, iq):

        try:
            if iq['type'] == 'error':
                print 'ERROR', iq.toXml().encode('utf-8')

            self.server.queueRequest(iq)
        except Exception, e:
            print 'ERROR', e.__class__.__name__, e


class JabberServer(RepositoryWorker):

    def __init__(self, repository):

        super(JabberServer, self).__init__('__jabber__', repository)
        self._repoId, x, x = repository.getSchemaInfo()

    def start(self, client):

        self.client = client
        client.server = self

        super(JabberServer, self).start()

    def findShare(self, view, collection, repoId, peerId):

        userid, server, resource = canonize(peerId, self.client.host)
        for account in JabberAccount.getKind(view).iterItems():
            if (account.userid == userid and
                account.server == server and
                account.resource == resource):
                break
        else:
            account = JabberAccount(itsView=view, userid=userid,
                                    server=server, resource=resource,
                                    user=User(itsView=view, name=userid))
            view.commit()

        acl = collection.getACL('p2p', None)
        if acl is None or not acl.verify(account.user, Permissions.READ):
            raise AccessDeniedError

        for share in collection.shares:
            if isinstance(share, JabberShare):
                if share.repoId == repoId:
                    return share

        share = JabberShare(itsView=view, repoId=repoId)
        share.conduit = JabberConduit(itsParent=share, peerId=peerId,
                                      account=view[self.client.account])
        share.format = CloudXMLDiffFormat(itsParent=share)
        share.contents = collection
        share.localVersion = view.itsVersion + 1
        view.commit()

        return share

    def computeChanges(self, view, fromVersion, collection, share):

        if fromVersion > 0:
            view.refresh(None, fromVersion, False)

        attributes = {}
        changes = {}
        origKeys = set()
        references = set()

        for key in collection.iterkeys():
            for cloud in view.kindForKey(key).getClouds('sharing'):
                cloud.getKeys(key, 'sharing', origKeys, references)

        if fromVersion > 0:
            view.refresh(None, None, False)

            currKeys = set()
            references = set()
            for key in collection.iterkeys():
                for cloud in view.kindForKey(key).getClouds('sharing'):
                    cloud.getKeys(key, 'sharing', currKeys, references)

            for (uItem, itemVersion, kind, status, values, references,
                 prevKind) in view.mapHistory(fromVersion, view.itsVersion):
                if uItem in origKeys or uItem in currKeys:

                    if uItem not in changes:
                        _changes, s = set(), status
                    else:
                        _changes, s = changes[uItem]

                    if status & CItem.DELETED:
                        if uItem not in origKeys:
                            continue
                    else:
                        uKind = kind.itsUUID
                        if uKind not in attributes:
                            attributes[uKind] = share.getSharedAttributes(kind)
                        if uItem not in origKeys:
                            s |= CItem.NEW
                            
                    if status & CItem.DELETED:
                        _changes = None
                    elif s & CItem.NEW:
                        status = CItem.NEW
                        _changes = attributes[kind.itsUUID]
                    else:
                        names = attributes[kind.itsUUID]
                        values = [value for value in values if value in names]
                        references = [ref for ref in references if ref in names]
                        if not (values or references):
                            continue

                        _changes.update(values)
                        _changes.update(references)

                    changes[uItem] = (_changes, status)

        else:
            for key in origKeys:
                kind = view.kindForKey(key)
                uKind = kind.itsUUID
                _changes = attributes.get(uKind)
                if _changes is None:
                    _changes = share.getSharedAttributes(kind)
                    attributes[uKind] = _changes
                changes[key] = (_changes, 0)

        return changes

    def processRequest(self, view, iq):

        iqType = iq['type']

        if iqType == 'get':
            view = self._processGet(view, iq)
        elif iqType == 'result':
            view = self._processResult(view, iq)
        elif iqType == 'error':
            view = self._processError(view, iq)
        else:
            raise NotImplementedError, iqType

        return view

    def _processGet(self, view, iq):

        self.client.output("processing request")

        to = iq['from']
        id = iq['id']
        responses = []

        try:
            if view is None:
                view = self._repository.createView("Jabber")

            for elem in iq.query.elements():
                method = getattr(self, '_get_' + elem.name, None)
                if method is not None:
                    responses.append(method(view, iq, elem.attributes))
                else:
                    raise NotImplementedError, elem.name

        except Exception, e:
            iq = client.IQ(self.client.xmlstream, "error")
            iq.addElement(("jabber:x:chandler", "query"))
            cls = e.__class__
            error = iq.query.addElement("error", None, traceback.format_exc())
            error['class'] = "%s.%s" %(cls.__module__, cls.__name__)
            error['args'] = ','.join(map(str, e.args))
            responses = [iq]

        for response in responses:
            response['id'] = id
            reactor.callFromThread(response.send, to)

        self.client.output(None)

        return view

    def _processResult(self, view, iq):

        self.client.output("processing result")

        try:
            if view is None:
                view = self._repository.createView("Jabber")

            for elem in iq.query.elements():
                method = getattr(self, '_result_' + elem.name, None)
                if method is not None:
                    method(view, iq, elem, elem.attributes)
                else:
                    raise NotImplementedError, elem.name

        except Exception, e:
            print traceback.format_exc()

        return view

    def _processError(self, view, iq):

        self.client.output("processing error")

        error = iq.query.error
        className = error['class']

        if className == 'p2p.errors.RepositoryMismatchError':
            args = error['args'].split(',')
            view.refresh(None, None, False)
            repoId = UUID(args[0])
            for share in JabberShare.getKind(view).iterItems():
                if share.repoId == repoId:
                    share.delete()
            view.commit()

    def _get_sync(self, view, iq, args):

        try:
            if 'toRepoId' in args and UUID(args['toRepoId']) != self._repoId:
                raise RepositoryMismatchError, args['toRepoId']

            view.refresh(None, None, False)

            repoId = UUID(args['fromRepoId'])
            name = args['name']
            version = int(args.get('version', '0'))

            if 'uuid' in args:
                uuid = UUID(args['uuid'])
                collection = view.find(uuid)
                if collection is None:
                    raise NameError, ('no such collection', uuid)
            else:
                sidebar = schema.ns('osaf.app', view).sidebarCollection
                for collection in sidebar:
                    if collection.displayName == name:
                        break
                else:
                    raise NameError, ('no such collection', name)

            share = self.findShare(view, collection, repoId, iq['from'])

            iq = client.IQ(self.client.xmlstream, "result")
            query = iq.addElement(("jabber:x:chandler", "query"))
            sync = query.addElement('sync')
            sync['name'] = name

            dom = DomishDOM()
            keys = set()
            changes = self.computeChanges(view, version, collection, share)
            for key, (_changes, status) in changes.iteritems():
                if key not in keys:
                    item = sync.addElement('item')
                    item['uuid'] = key.str64()
                    if status & CItem.DELETED:
                        item['status'] = 'deleted'
                    else:
                        if key in collection:
                            item['status'] = 'member'
                        share.format.exportProcess(dom, key, item,
                                                   changes, keys)
                elif key in collection:
                    item = sync.addElement('item')
                    item['uuid'] = key.str64()
                    item['status'] = 'member'

            sync['fromRepoId'] = self._repoId.str64()
            sync['toRepoId'] = repoId.str64()
            sync['version'] = str(view.itsVersion)
            sync['uuid'] = collection.itsUUID.str64()

        except:
            view.cancel()
            raise

        share.localVersion = view.itsVersion + 1
        share.established = True
        view.commit()

        return iq

    def _result_sync(self, view, iq, sync, args):

        try:
            view.refresh(None, None, False)

            if 'toRepoId' in args and UUID(args['toRepoId']) != self._repoId:
                raise RepositoryMismatchError, args['toRepoId']

            repoId = UUID(args['fromRepoId'])
            uuid = UUID(args['uuid'])
            version = int(args['version'])
            collection = view.find(uuid)

            if collection is None:
                collection = pim.SmartCollection(itsView=view, _uuid=uuid,
                                                 displayName=args['name'])
                schema.ns("osaf.app", view).sidebarCollection.add(collection)

                # for now, grant READ to everyone
                acl = ACL()
                acl.append(ACE(schema.ns('p2p', view).all.itsUUID,
                               Permissions.READ))
                collection.setACL(acl, 'p2p')
                isNew = True
            else:
                isNew = False

            share = self.findShare(view, collection, repoId, iq['from'])
            format = share.format

            if isNew:
                share.localVersion = view.itsVersion + 1
            else:
                changes = self.computeChanges(view, share.localVersion,
                                              collection, share)
                if not changes:
                    share.localVersion = view.itsVersion + 1

            dom = DomishDOM()
            share.remoteVersion = version
            view.deferDelete()

            for itemElement in sync.elements():
                attributes = itemElement.attributes
                status = attributes.get('status')
                if status == 'deleted':
                    item = view.findUUID(attributes['uuid'])
                    if item is not None:
                        item.delete()
                else:
                    child = itemElement.firstChildElement()
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
        self.client.output("%s synchronized" %(collection.displayName))

        to = iq['from']
        iq = client.IQ(self.client.xmlstream, 'result')
        iq.addElement(('jabber:x:chandler', 'query'))
        version = iq.query.addElement('version')
        version['fromRepoId'] = self._repoId.str64()
        version['toRepoId'] = repoId.str64()
        version['uuid'] = collection.itsUUID.str64()
        version['version'] = str(share.localVersion)
        reactor.callFromThread(iq.send, to)

    def _result_version(self, view, iq, elem, args):

        try:
            view.refresh(None, None, False)

            repoId = UUID(args['fromRepoId'])
            uuid = UUID(args['uuid'])
            version = int(args['version'])
            collection = view.find(uuid)

            if collection is None:
                raise NameError, ('no such collection', uuid)

            share = self.findShare(view, collection, repoId, iq['from'])
            share.remoteVersion = version
        except:
            view.cancel()
            raise

        view.commit()
        self.client.output(None)
