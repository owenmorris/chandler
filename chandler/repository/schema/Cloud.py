
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from repository.item.Item import Item
from repository.item.ItemRef import RefDict


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


class Endpoint(Item):

    def getItems(self, item, items):

        policy = self.includePolicy

        if policy == 'byValue':
            items[item._uuid] = item

        elif policy == 'byCloud':
            cloud = self.getAttributeValue('cloud', default=None,
                                           _attrDict=self._references)

            if cloud is None:
                cloud = item.itsKind.getClouds()
                if not cloud:
                    raise TypeError, 'No cloud for %s' %(item.itsKind.itsPath)
                cloud = cloud[0]

            cloud.getItems(item, items)

        else:
            raise NotImplementedError, policy
