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


import urlparse


class URL(object):
    """
    A URL class whose implementation wraps the urlparse python module.

    A URL is made of 7 parts, accessible via read-only properties: scheme,
    host, port, parameters, path and fragment according to the standard
    syntax: C{scheme://host:port/path;parameters?query#fragment}

    Unset parts are C{None}.

    Instances of this class are intended to be immutable. Instead of
    modifying this instance, the L{join} and L{make} methods are provided to
    create new URL instances based on this one.

    This class is intended to be final.
    """
    
    __slots__ = ('_scheme', '_host', '_port', '_path',
                 '_parameters', '_query', '_fragment')

    def __init__(self, url):
        """
        Construct a URL instance from a url string.
        """

        (self._scheme, location, self._path,
         self._parameters, self._query,
         self._fragment) = urlparse.urlparse(url)

        lc = location.rfind(':')
        if lc >= 0:
            try:
                self._port = int(location[lc+1:])
                self._host = location[:lc]
            except ValueError:
                self._port = None
                self._host = location
        else:
            self._port = None
            self._host = location

    def __str__(self):

        if self._port is not None:
            location = "%s:%d" %(self._host, self._port)
        else:
            location = self._host

        return urlparse.urlunparse((self._scheme, location, self._path,
                                    self._parameters, self._query,
                                    self._fragment))

    def __repr__(self):

        return "<URL: %s>" % self.__str__()

    def __eq__(self, other):

        return isinstance(other, URL) and str(self).__eq__(str(other))

    def __ge__(self, other):

        return isinstance(other, URL) and str(self).__ge__(str(other))

    def __gt__(self, other):

        return isinstance(other, URL) and str(self).__gt__(str(other))

    def __le__(self, other):

        return isinstance(other, URL) and str(self).__le__(str(other))

    def __lt__(self, other):

        return isinstance(other, URL) and str(self).__lt__(str(other))

    def __ne__(self, other):

        if isinstance(other, URL):
            return str(self).__ne__(str(other))

        return True

    def join(self, url):
        """
        Create a URL instance from a url string using this one for defaults.

        Returns a new URL by combining this url and the C{url} argument.
        This method uses components of this url, in particular the
        addressing scheme, the network location and the path and attempts
        to provide a resulting URL with an absolute path.
        """

        return URL(urlparse.urljoin(self.__str__(), url))

    def make(self, scheme=None, host=None, port=None,
             path=None, parameters=None, query=None, fragment=None):
        """
        Create a URL instance from a url parts using this one for defaults.

        Returns a new URL by combining the parts provided with the parts
        known for this URL.
        """

        if scheme is None:
            scheme = self._scheme
        if host is None:
            host = self._host
        if port is None:
            port = self._port
        if path is None:
            path = self._path
        if parameters is None:
            parameters = self._parameters
        if query is None:
            query = self._query
        if fragment is None:
            fragment = self._fragment

        if port is not None:
            location = "%s:%d" %(host, port)
        else:
            location = host

        return URL(urlparse.urlunparse((scheme, location, path,
                                        parameters, query, fragment)))

    scheme = property(lambda self: self._scheme or None)
    host = property(lambda self: self._host or None)
    port = property(lambda self: self._port)
    path = property(lambda self: self._path or None)
    parameters = property(lambda self: self._parameters or None)
    query = property(lambda self: self._query or None)
    fragment = property(lambda self: self._fragment or None)
