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


"""
The beginning of a search module.

The initial purpose of this module is to transform search results from
Lucene into a set of Note-based items.

Right now this is hardcoded for non-Note types like Location and
EmailAddress. Eventually we'd like this to be pluggable, so that any
arbitrary result can be transformed into a Note-based item.
"""

from osaf.pim import Location, EmailAddress, Note
from itertools import chain

def processResults(results):
    """
    a generator that returns Notes-based items based on Lucene results

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

