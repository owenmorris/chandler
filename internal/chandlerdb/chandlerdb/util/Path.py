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


from chandlerdb.util.c import UUID


class Path(object):
    """
    A path to an item in a repository.

    A path can be absolute to a repository; it then starts with C{//}.
    A path can be absolute to a repository root; it then starts with C{/}.
    A path can be relative to an item when it doesn't start with C{/}.
    """
    
    def __init__(self, *args):
        """
        Construct a path.

        See L{set} method for more details on path construction.
        A path can be used as an iterator over its constituent names.
        """
        
        super(Path, self).__init__()
        self.set(*args)

    def __repr__(self):

        path = ''
        i = 0
        
        for name in self._names:
            if i > 1 or i == 1 and path[0] != '/':
                path += '/'
            if isinstance(name, UUID):
                path += '{%s}' %(name.str64())
            else:
                path += name
            i += 1

        return path

    def __getslice__(self, start, end):

        return Path(*self._names.__getslice__(start, end))

    def __getitem__(self, index):

        return self._names[index]

    def __len__(self):

        return self._names.__len__()

    def __iter__(self):

        return self._names.__iter__()

    def set(self, *args):
        """
        Any number of arguments are combined to form a list of names, a path.
        Individual Arguments are split along C{/} characters allowing for paths
        to be constructed from path strings.
        Ending C{/} characters are stripped.
        """
        
        self._names = []
        first = True
        
        for arg in args:

            if isinstance(arg, Path):
                self._names.extend(arg._names)

            elif isinstance(arg, UUID):
                self._names.append(arg)

            elif arg:
                
                if arg.startswith('//'):
                    if first:
                        self._names.append('//')
                    arg = arg[2:]

                elif arg.startswith('/'):
                    if first:
                        self._names.append('/')
                    arg = arg[1:]

                if arg.endswith('/'):
                    arg = arg[:-1]

                if arg:
                    for arg in arg.split('/'):
                        if arg.startswith('{'):
                            arg = UUID(arg[1:-1])
                        self._names.append(arg)

                first = False

    def append(self, name):
        """
        Add a name to this path.

        C{name} should be a string without C{/} characters.

        @param name: the name to add
        @type name: a string
        """

        if not isinstance(name, UUID) and name.startswith('{'):
            name = UUID(name[1:-1])
            
        self._names.append(name)

    def extend(self, path):
        """
        Concatenate two paths.

        This path is augmented with C{path}'s names.
        Leading '/' are not stripped.

        @param path: the path to extend this path with
        @type path: a C{Path} instance
        """

        self._names.extend(path._names)

    def pop(self, index=-1):
        """
        Remove a name from this path.

        @param index: the optional index of the name to rename to remove; by
        default, the last name is removed.
        @type index: integer
        @return: the name removed
        """

        return self._names.pop(index)

    def normalize(self):
        """
        Create a normalized path from this path.

        Redundant C{..} and C{.} names are removed.

        @return: a new path instance
        """

        names = []
        for name in self._names:
            if name == '.':
                continue
            if name == '..':
                if names and not names[-1] in ['/', '//', '..']:
                    names.pop()
                else:
                    names.append(name)
                continue
            names.append(name)

        return Path(*names)

    def __eq__(self, other):

        return (isinstance(other, Path) and
                self.normalize()._names.__eq__(other.normalize()._names))

    def __ge__(self, other):

        return (isinstance(other, Path) and
                self.normalize()._names.__ge__(other.normalize()._names))

    def __gt__(self, other):

        return (isinstance(other, Path) and
                self.normalize()._names.__gt__(other.normalize()._names))

    def __le__(self, other):

        return (isinstance(other, Path) and
                self.normalize()._names.__le__(other.normalize()._names))

    def __lt__(self, other):

        return (isinstance(other, Path) and
                self.normalize()._names.__lt__(other.normalize()._names))

    def __ne__(self, other):

        if isinstance(other, Path):
            return self.normalize()._names.__ne__(other.normalize()._names)

        return True
