#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


from repository.item.Item import Item
from repository.item.Collection import Collection, CollectionClass


class Movie(Item):

    def compareFrench(self, other):

        if self.frenchTitle < other.frenchTitle:
            return -1
        elif self.frenchTitle > other.frenchTitle:
            return 1
        else:
            return 0

    def onItemCopy(self, view, original):

        print 'copied', self.title, 'from', original.itsUUID

    def kindChanged(self, op, kind, item, dirties):

        self.monitorAttribute = 'kind'
        print self, 'kindChanged', op, self, kind, item, dirties

    def itemChanged(self, op, item, dirties):

        print self, 'itemChanged', op, item, dirties

    def onCollectionNotification(self, op, collection, name, other, dirties):

        print self, 'onCollectionNotification', op, collection, name, other, dirties

    def titleChanged(self, op, name):

        count = getattr(self, '_titleChanged', 0)
        self._titleChanged = count + 1

    def plus(self, op, name):

        print 'plus', op, name
        self.sum = self.a + self.b


class Cartoon(Movie):
    pass


class Movies(Collection):

    __metaclass__ = CollectionClass
    __collection__ = 'collection'
