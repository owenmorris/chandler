
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

    def getItems(self, item, items=None, references=None, cloudAlias=None):
        """
        Gather all items in the cloud.

        Items are found at each endpoint of this cloud and are included into
        the returned result set and the optional C{items} and C{references}
        dictionaries according to the following endpoint policies:

            - C{byValue}: the item is added to the result set and is added
              to the C{items} dictionary.

            - C{byRef}: the item is not added to the result set but is added
              to the C{references} dictionary.

            - C{byCloud}: the item is added to the result set and is used
              as an entrypoint for a cloud gathering operation. The cloud
              used is determined in this order:

                  - the cloud specified on the endpoint

                  - the cloud obtained by the optional C{cloudAlias}

                  - the first cloud specified for the item's kind

              The results of the cloud gathering operation are merged with
              the current one.

        @param item: the entry point of the cloud.
        @type item: an C{Item} instance
        @param items: an optional dictionary keyed on the item UUIDs that
        also receives all items in the cloud.
        @type items: dict
        @param references: an optional dictionary keyed on the item UUIDs
        that receives all items referenced from an endpoint with a C{byRef}
        include policy.
        @type references: dict
        @param cloudAlias: the optional alias name to use for C{byCloud}
        policy endpoints where the cloud is unspecified.
        @type cloudAlias: a string
        @return: the list of all items considered part of the cloud.
        """

        if not item.isItemOf(self.kind):
            raise TypeError, '%s is not of a kind this cloud (%s) understands' %(item.itsPath, self.itsPath)

        if items is None:
            items = {}
        if references is None:
            references = {}

        if not item._uuid in items:
            items[item._uuid] = item
            results = [item]
        else:
            results = []

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
                        results.extend(endpoint.getItems(value, items,
                                                         references,
                                                         cloudAlias))
                elif isinstance(value, RefDict) or isinstance(value, list):
                    for other in value:
                        if other is not None and other._uuid not in items:
                            results.extend(endpoint.getItems(other, items,
                                                             references,
                                                             cloudAlias))
                else:
                    raise TypeError, type(value)

        return results

    def copyItems(self, item, name=None, parent=None,
                  copies=None, cloudAlias=None):
        """
        Copy all items in the cloud.

        Items are first gathered as documented in L{getItems}. They are then
        copied as follows:

            - items in the result set returned by L{getItems} are copied and
              added to the result set copy in the order they occur in the
              original result set.

            - references to items in the original result set are copied as
              references to their corresponding copies and are set on the
              item copies everywhere they occur.

            - references to items in the C{references} dictionary upon
              returning from L{getItems}, that is, references to items that
              are not considered part of the cloud but are nonetheless
              referenced by items in it are set unchanged on the item copies
              everywhere they occur.

            - any other item references are not set on the item copies.
        
        @param item: the entry point of the cloud.
        @type item: an C{Item} instance
        @param copies: an optional dictionary keyed on the original item
        UUIDs that also received all items copies.
        @type items: dict
        @param cloudAlias: the optional alias name to use for C{byCloud}
        policy endpoints where the cloud is unspecified.
        @type cloudAlias: a string
        @return: the list of all item copies considered part of the cloud.
        """

        items = {}
        references = {}
        copying = self.getItems(item, items, references, cloudAlias)
        
        if copies is None:
            copies = {}

        copy = item.copy(name, parent, copies, 'remove')
        results = [copy]

        def copyValue(item, name, value):
            uuid = value._uuid
            if uuid in items:
                if uuid in copies:
                    return copies[uuid]
                else:
                    value = value.copy(None, parent, copies, 'remove')
                    results.append(value)
                    return value
            elif uuid in references:
                return value
            else:
                return None

        for item in copying:
            if not item._uuid in copies:
                copy = item.copy(None, parent, copies, 'remove')
            else:
                copy = copies[item._uuid]
                
            refs = copy._references
            for name, value in item.iterAttributeValues(referencesOnly=True):
                if isinstance(value, Item):
                    value = copyValue(copy, name, value)
                    if value is not None and name not in refs:
                        copy.setAttributeValue(name, value, _attrDict=refs)
                elif value is None:
                    copy.setAttributeValue(name, None, _attrDict=refs)
                else:
                    if name in refs:
                        refDict = refs[name]
                    else:
                        refDict = refs[name] = copy._refDict(name)
                        
                    for v in value:
                        v = copyValue(copy, name, v)
                        if v is not None and v not in refDict:
                            refDict.append(v)

        return results

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

    def getItems(self, item, items, references, cloudAlias):

        policy = self.includePolicy
        results = []
        
        if policy == 'byValue':
            if not item._uuid in items:
                items[item._uuid] = item
                results.append(item)

        elif policy == 'byRef':
            references[item._uuid] = item

        elif policy == 'byCloud':
            cloud = self.getAttributeValue('cloud', default=None,
                                           _attrDict=self._references)
            if cloud is None:
                kind = item._kind
                if cloudAlias is None:
                    cloudAlias = self.getAttributeValue('cloudAlias',
                                                        default=None,
                                                        _attrDict=self._values)
                if cloudAlias is not None:
                    cloud = kind.getCloud(cloudAlias)
                else:
                    cloud = kind.getClouds().first()

            results.extend(cloud.getItems(item, items, references, cloudAlias))

        else:
            raise NotImplementedError, policy

        return results

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
