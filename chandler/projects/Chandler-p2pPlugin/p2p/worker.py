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


from application import schema
from chandlerdb.item.c import CItem
from osaf.pim import has_stamp
from osaf.sharing import SharedItem

from repository.persistence.Repository import RepositoryWorker
from repository.item.Access import AccessDeniedError, Permissions



class Worker(RepositoryWorker):

    def __init__(self, name, repository):

        super(Worker, self).__init__(name, repository)

        self._name = name
        self._repoId, x, x = repository.getSchemaInfo()

    def start(self, client):

        self.client = client
        client.worker = self

        super(Worker, self).start()

    def getView(self, view):

        if view is None:
            view = self._repository.createView(self._name)

        return view

    def findCollection(self, view, name, uuid):

        if uuid is not None:
            collection = view.find(uuid)
            if collection is not None:
                return collection, collection.displayName, uuid
            raise NameError, ('no such collection', uuid)

        else:
            sidebar = schema.ns('osaf.app', view).sidebarCollection
            for collection in sidebar:
                if collection.displayName == name:
                    return collection, name, collection.itsUUID
            raise NameError, ('no such collection', name)

    def findShare(self, view, collection, repoId, peerId):

        account = self.findAccount(view, peerId)

        acl = collection.getACL('p2p', None)
        if acl is None or not acl.verify(account.user, Permissions.READ):
            raise AccessDeniedError

        for share in SharedItem(collection).shares:
            if isinstance(share, self.shareClass):
                if share.repoId is None:
                    if (share.ackPending and
                        share.contents is collection and
                        share.conduit.account is account and
                        share.conduit.peerId == peerId):
                        share.repoId = repoId
                        return share
                elif share.repoId == repoId:
                    return share

        share = self.shareClass(view, view[self.client.account], repoId, peerId)
        share.contents = collection
        if not has_stamp(collection, SharedItem):
            SharedItem(collection).add()
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
