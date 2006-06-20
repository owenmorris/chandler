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


def valueLookup(collection, indexName, attrName, value, multiple=False):

    view = collection.itsView

    def _compare(uuid):
        # Use the new method for getting an attribute value without
        # actually loading an item:
        attrValue = view.findValue(uuid, attrName)
        return cmp(str(value), str(attrValue))

    firstUUID = collection.findInIndex(indexName, 'first', _compare)

    if firstUUID is None: # We're done
        if multiple:
            return []
        else:
            return None

    if multiple: # Let's see if there are more than one
        lastUUID = collection.findInIndex(indexName, 'last', _compare)
        results = []
        for uuid in collection.iterindexkeys(indexName, firstUUID, lastUUID):
            results.append(view[uuid])
        return results

    else:
        return view[firstUUID]


