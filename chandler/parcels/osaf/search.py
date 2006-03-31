"""
The beginning of a search module.

The initial purpose of this module is to transform search results from
PyLucene into a set of Note-based items.

Right now this is hardcoded for non-Note types like Location and
EmailAddress. Eventually we'd like this to be pluggable, so that any
arbitrary result can be transformed into a Note-based item.
"""

from osaf.pim import Location, EmailAddress, Note

def processResults(results):
    """
    a generator that returns Notes-based items based on PyLucene results

    At the moment there are no guarantees that the same item won't be
    returned more than once.
    """
    for item,attribute in results:
        if isinstance(item, Note):
            yield item
                               
        if isinstance(item, Location):
            for event in item.eventsAtLocation:
                yield event

        if isinstance(item, EmailAddress):
            for event in chain(item.messagesBcc,
                               item.messagesCc,
                               item.messagesFrom,
                               item.messagesReplyTo,
                               item.messagesTo):
                yield event

