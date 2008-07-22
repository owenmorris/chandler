#   Copyright (c) 2004-2008 Open Source Applications Foundation
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

__all__ = [
    'register',
    'unregister',
    'callCallbacks',
    'needsCalling',
    'UPDATE',
    'UNSUBSCRIBEDCOLLECTIONS',
]

UPDATE = 1
UNSUBSCRIBEDCOLLECTIONS = 2

registeredCallbacks = {
    UPDATE : { },
    UNSUBSCRIBEDCOLLECTIONS : { },
}

def register(event, func, *args):
    global registeredCallbacks
    if func not in registeredCallbacks[event]:
        registeredCallbacks[event][func] = args

def unregister(event, func):
    global registeredCallbacks
    try:
        del registeredCallbacks[event][func]
    except KeyError:
        pass

def callCallbacks(event, **kwds):
    for (func, args) in registeredCallbacks[event].items():
        func(*args, **kwds)

def needsCalling(event):
    return len(registeredCallbacks[event]) > 0

# An example callback which simply prints to stdout:
# def printIt(*args, **kwds):
#     print args, kwds
# register(sharing.UPDATE, printIt)

