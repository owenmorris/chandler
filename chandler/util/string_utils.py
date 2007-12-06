#   Copyright (c) 2007 Open Source Applications Foundation
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

def nocase_replace(msg, old, new):
    """
    Like str.replace, but case insensitive find.
    
    >>> s = 'Aabb'
    >>> nocase_replace(s, 'a', 'cc')
    'ccccbb'
    >>> s = 'Hello World! The WORLD is not Enough!'
    >>> nocase_replace(s, 'world', 'Moon')
    'Hello Moon! The Moon is not Enough!'
    >>> nocase_replace(s, '', 'Moon')
    Traceback (most recent call last):
    ...
    ValueError: Need a non-empty string to search for
    >>> s = ''
    >>> nocase_replace(s, 'a', 'cc')
    ''
    """
    if not old:
        raise ValueError('Need a non-empty string to search for')
    if not msg:
        return msg
    
    s = msg.lower()
    o = old.lower()
    ret = []
    i = 0
    j = s.find(o)
    oldLen = len(old)
    
    while j > -1:
        ret.append(msg[i:j])
        ret.append(new)
        i = j + oldLen
        j = s.find(o, i)
    ret.append(msg[i:])

    return ''.join(ret)

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
