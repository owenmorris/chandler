#   Copyright (c) 2006 Open Source Applications Foundation
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
from osaf.sharing import conduits, shares
from repository.item.Principal import Principal


def findAccounts(view):
    return [account for account in Account.iterItems(view)]


def findDefaultAccounts(view):
    return [account for account in Account.iterItems(view)
            if account.default]


def findLoggedInAccounts(view):
    return [account for account in Account.iterItems(view)
            if account.isLoggedIn()]


class User(schema.Item, Principal):

    name = schema.One(schema.Text)
    accounts = schema.Sequence(otherName='user', initialValue=[])


class Group(schema.Item, Principal):

    name = schema.One(schema.Text)


class AllGroup(Group):

    def isMemberOf(self, pid):
        return True


class Account(schema.Item):

    userid = schema.One(schema.Text)
    server = schema.One(schema.Importable)
    protocol = schema.One(schema.Symbol)
    user = schema.One(otherName='accounts', initialValue=None)
    default = schema.One(schema.Boolean, initialValue=False)
    autoLogin = schema.One(schema.Boolean, initialValue=False)
    conduits = schema.Sequence(otherName='account')

    _clients = {}

    def __init__(self, *args, **kwds):

        super(Account, self).__init__(*args, **kwds)

        if self.user is None:
            self.user = User(itsView=self.itsView, name=self.userid)

    def login(self, printf, autoLogin=False):
        raise NotImplementedError, "%s.login" %(type(self))

    def isLoggedIn(self):
        raise NotImplementedError, "%s.isLoggedIn" %(type(self))

    def subscribe(self, name, remoteId):
        raise NotImplementedError, "%s.subscribe" %(type(self))

    def sync(self, share):
        raise NotImplementedError, "%s.sync" %(type(self))

    def _getClient(self):
        return type(self)._clients.get(self.itsUUID)

    def _setClient(self, client):
        type(self)._clients[self.itsUUID] = client

    client = property(_getClient, _setClient)


class Conduit(conduits.Conduit):

    account = schema.One(otherName='conduits')


class Share(shares.Share):

    repoId = schema.One(schema.UUID)
    remoteVersion = schema.One(schema.Long)
    localVersion = schema.One(schema.Long)

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None):

        return self.conduit.account.sync(self)
