
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import libxml2, re

from repository.item.Item import Item
from repository.item.ItemRef import RefDict
from repository.remote.CloudFilter import CloudFilter, EndpointFilter
from repository.remote.CloudFilter import RefHandler
from repository.persistence.RepositoryError import NoSuchItemError


class Cloud(Item):

    def getItems(self, item, items=None):

        if not item.isItemOf(self.kind):
            raise TypeError, '%s is not of a kind this cloud (%s) understands' %(item.itsPath, self.itsPath)

        if items is None:
            items = { item._uuid: item }
        elif not item._uuid in items:
            items[item._uuid] = item

        for endpoint in self.endpoints:
            value = item
            for name in endpoint.attribute:
                if isinstance(value, RefDict) or isinstance(value, list):
                    value = [v.getAttributeValue(name, default=None,
                                                 _attrDict=v._references)
                             for v in value if v is not None]
                else:
                    value = value.getAttributeValue(name, default=None,
                                                    _attrDict=value._references)
                    if value is None:
                        break

            if value is not None:
                if isinstance(value, Item):
                    if value._uuid not in items:
                        endpoint.getItems(value, items)
                elif isinstance(value, RefDict) or isinstance(value, list):
                    for other in value:
                        if other is not None and other._uuid not in items:
                            endpoint.getItems(other, items)
                else:
                    raise TypeError, type(value)

        return items

    def getEndpoints(self, name, index=0):

        endpoints = []
        for endpoint in self.endpoints:
            names = endpoint.attribute
            if index < len(names) and names[index] == name:
                endpoints.append(endpoint)

        return endpoints

    def writeItems(self, uuid, version, generator, xml=None, uuids=None):

        if uuids is None:
            uuids = {}
            
        if not uuid in uuids:
            store = self.itsView.store

            uuids[uuid] = uuid
            if xml is None:
                doc = store.loadItem(version, uuid)
                if doc is None:
                    raise NoSuchItemError, (uuid, version)
                
                xml = doc.getContent()

            filter = CloudFilter(self, store, uuid, version, generator)
            filter.parse(xml, uuids)


class Endpoint(Item):

    def getItems(self, item, items):

        policy = self.includePolicy

        if policy == 'byValue':
            items[item._uuid] = item

        elif policy == 'byCloud':
            cloud = self.getAttributeValue('cloud', default=None,
                                           _attrDict=self._references)
            if cloud is None:
                cloud = kind.getClouds()
                if not cloud:
                    raise TypeError, 'No cloud for %s' %(kind.itsPath)
                cloud = cloud[0]

            cloud.getItems(item, items)

        else:
            raise NotImplementedError, policy

    def writeItems(self, index, uuid, version, generator, xml, uuids):

        names = self.attribute

        if index == len(names):
            if not uuid in uuids:
                policy = self.includePolicy

                if policy == 'byValue':
                    filter = EndpointFilter(self, self.itsView.store,
                                            uuid, version, generator)
                    filter.parse(xml)
                    uuids[uuid] = uuid

                elif policy == 'byCloud':
                    cloud = self.getAttributeValue('cloud', default=None,
                                                   _attrDict=self._references)
                    if cloud is None:
                        match = self.kindExp.match(xml, xml.index("<kind "))
                        kind = self.itsView[UUID(match.group(1))]
                        cloud = kind.getClouds()
                        if not cloud:
                            raise TypeError, 'No cloud for %s' %(kind.itsPath)
                        cloud = cloud[0]

                    cloud.writeItems(uuid, version, generator, xml, uuids)

                else:
                    raise NotImplementedError, policy

        else:
            handler = RefHandler(self, names[index], uuid, version)
            handler.parse(xml)

            if handler.values is not None:
                store = self.itsView.store
                for uuid in handler.values:
                    doc = store.loadItem(version, uuid)
                    if doc is None:
                        raise NoSuchItemError, (uuid, version)
                    xml = doc.getContent()
                    self.writeItems(index + 1, uuid, version, generator,
                                    xml, uuids)

    kindExp = re.compile('<kind type="uuid">(.*)</kind>')
