
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class Path(object):
    '''A path to an item in a repository.

    A path can be absolute to a repository in which case it starts with //.
    A path can be absolute to a repository root in which case it start with /.
    A path is relative to an item when it doesn't begin with '/' and is used in
    conjunction with an item, as in an item's find method.'''
    
    def __init__(self, *args):
        '''Construct a path.

        Any number of arguments are combined to for a list of names, a path.
        Individual Arguments are split along '/' characters allowing for paths
        to be constructed from path strings.
        Ending '/' are stripped.
        A path can be used as an iterator over its constituent names.'''
        
        super(Path, self).__init__()
        
        self._names = []

        for arg in args:
            if arg.startswith('//'):
                self._names.append('//')
                arg = arg[2:]
            elif arg[0] == '/':
                self._names.append('/')
                arg = arg[1:]

            if arg.endswith('/'):
                arg = arg[:-1]

            if not arg == '':
                self._names.extend(arg.split('/'))

    def __repr__(self):

        path = ''
        i = 0
        
        for name in self._names:
            if i > 1 or i == 1 and path[0] != '/':
                path += '/'
            path += name
            i += 1

        return path

    def __getslice__(self, start, end):

        return apply(Path, self._names.__getslice__(start, end))

    def __getitem__(self, index):

        return self._names[index]

    def __len__(self):

        return self._names.__len__()

    def __iter__(self):

        return self._names.__iter__()

    def set(self, *args):

        self._names[:] = args

    def append(self, name):
        'Extend this path appending name it.'
        
        self._names.append(name)

    def extend(self, path):
        'Concatenate two paths. Leading '/' are not stripped.'

        self._names.extend(path._names)

    def pop(self, i=-1):

        return self._names.pop(i)

    def canonize(self):

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
                self.canonize()._names.__eq__(other.canonize()._names))

    def __ge__(self, other):

        return (isinstance(other, Path) and
                self.canonize()._names.__ge__(other.canonize()._names))

    def __gt__(self, other):

        return (isinstance(other, Path) and
                self.canonize()._names.__gt__(other.canonize()._names))

    def __le__(self, other):

        return (isinstance(other, Path) and
                self.canonize()._names.__le__(other.canonize()._names))

    def __lt__(self, other):

        return (isinstance(other, Path) and
                self.canonize()._names.__lt__(other.canonize()._names))

    def __ne__(self, other):

        return (isinstance(other, Path) and
                self.canonize()._names.__ne__(other.canonize()._names))
