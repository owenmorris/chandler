#
# DAV client library
#
# Copyright (C) 1998-2000 Guido van Rossum. All Rights Reserved.
# Written by Greg Stein. Given to Guido. Licensed using the Python license.
#
# This module is maintained by Greg and is available at:
#    http://www.lyra.org/greg/python/davlib.py
#
# Since this isn't in the Python distribution yet, we'll use the CVS ID
# for tracking:
#   $Id$
#

import httplib
import urllib
import string
import types
import mimetypes
import base64


INFINITY = 'infinity'
XML_DOC_HEADER = '<?xml version="1.0" encoding="utf-8"?>'
XML_CONTENT_TYPE = 'text/xml; charset="utf-8"'

# block size for copying files up to the server
BLOCKSIZE = 16384

class DAV(httplib.HTTPConnection):
  def setauth(self, username, password):
      self._username = username
      self._password = password

  def get(self, url, extra_hdrs={ }):
    return self._request('GET', url, extra_hdrs=extra_hdrs)

  def head(self, url, extra_hdrs={ }):
    return self._request('HEAD', url, extra_hdrs=extra_hdrs)

  def post(self, url, data={ }, body=None, extra_hdrs={ }):
    headers = extra_hdrs.copy()

    assert body or data, "body or data must be supplied"
    assert not (body and data), "cannot supply both body and data"
    if data:
      body = ''
      for key, value in data.items():
        if isinstance(value, types.ListType):
          for item in value:
            body = body + '&' + key + '=' + urllib.quote(str(item))
        else:
          body = body + '&' + key + '=' + urllib.quote(str(value))
      body = body[1:]
      headers['Content-Type'] = 'application/x-www-form-urlencoded'

    return self._request('POST', url, body, headers)

  def options(self, url='*', extra_hdrs={ }):
    return self._request('OPTIONS', url, extra_hdrs=extra_hdrs)

  def trace(self, url, extra_hdrs={ }):
    return self._request('TRACE', url, extra_hdrs=extra_hdrs)

  def put(self, url, contents,
          content_type=None, content_enc=None, extra_hdrs={ }):

    if not content_type:
      content_type, content_enc = mimetypes.guess_type(url)

    headers = extra_hdrs.copy()
    if content_type:
      headers['Content-Type'] = content_type
    if content_enc:
      headers['Content-Encoding'] = content_enc
    return self._request('PUT', url, contents, headers)

  def delete(self, url, extra_hdrs={ }):
    return self._request('DELETE', url, extra_hdrs=extra_hdrs)

  def propfind(self, url, body=None, depth=None, extra_hdrs={ }):
    headers = extra_hdrs.copy()
    headers['Content-Type'] = XML_CONTENT_TYPE
    if depth is not None:
      headers['Depth'] = str(depth)
    return self._request('PROPFIND', url, body, headers)

  def proppatch(self, url, body, extra_hdrs={ }):
    headers = extra_hdrs.copy()
    headers['Content-Type'] = XML_CONTENT_TYPE
    return self._request('PROPPATCH', url, body, headers)

  def mkcol(self, url, extra_hdrs={ }):
    return self._request('MKCOL', url, extra_hdrs=extra_hdrs)

  def move(self, src, dst, extra_hdrs={ }):
    headers = extra_hdrs.copy()
    headers['Destination'] = dst
    return self._request('MOVE', src, extra_hdrs=headers)

  def copy(self, src, dst, depth=None, extra_hdrs={ }):
    headers = extra_hdrs.copy()
    headers['Destination'] = dst
    if depth is not None:
      headers['Depth'] = str(depth)
    return self._request('COPY', src, extra_hdrs=headers)

  def lock(self, url, owner='', timeout=None, depth=None,
           scope='exclusive', type='write', extra_hdrs={ }):
    headers = extra_hdrs.copy()
    headers['Content-Type'] = XML_CONTENT_TYPE
    if depth is not None:
      headers['Depth'] = str(depth)
    if timeout is not None:
      headers['Timeout'] = timeout
    body = XML_DOC_HEADER + \
           '<DAV:lockinfo xmlns:DAV="DAV:">' + \
           '<DAV:lockscope><DAV:%s/></DAV:lockscope>' % scope + \
           '<DAV:locktype><DAV:%s/></DAV:locktype>' % type + \
           owner + \
           '</DAV:lockinfo>'
    return self._request('LOCK', url, body, extra_hdrs=headers)

  def unlock(self, url, locktoken, extra_hdrs={ }):
    headers = extra_hdrs.copy()
    if locktoken[0] != '<':
      locktoken = '<' + locktoken + '>'
    headers['Lock-Token'] = locktoken
    return self._request('UNLOCK', url, extra_hdrs=headers)

  def _request(self, method, url, body=None, extra_hdrs={}):
    "Internal method for sending a request."

    auth = 'Basic ' + string.strip(base64.encodestring(self._username + ':' + self._password))
    extra_hdrs['Authorization'] = auth
    self.request(method, url, body, extra_hdrs)
    return self.getresponse()


  #
  # Higher-level methods for typical client use
  #

  def allprops(self, url, depth=None):
    return self.propfind(url, depth=depth)

  def propnames(self, url, depth=None):
    body = XML_DOC_HEADER + \
           '<DAV:propfind xmlns:DAV="DAV:"><DAV:propname/></DAV:propfind>'
    return self.propfind(url, body, depth)

  def getprops(self, url, *names, **kw):
    assert names, 'at least one property name must be provided'
    if kw.has_key('ns'):
      xmlns = ' xmlns:NS="' + kw['ns'] + '"'
      ns = 'NS:'
      del kw['ns']
    else:
      xmlns = ns = ''
    if kw.has_key('depth'):
      depth = kw['depth']
      del kw['depth']
    else:
      depth = 0
    assert not kw, 'unknown arguments'
    body = XML_DOC_HEADER + \
           '<DAV:propfind xmlns:DAV="DAV:"' + xmlns + '><DAV:prop><' + ns + \
           string.joinfields(names, '/><' + ns) + \
           '/></DAV:prop></DAV:propfind>'
    return self.propfind(url, body, depth)

  def delprops(self, url, *names, **kw):
    assert names, 'at least one property name must be provided'
    if kw.has_key('ns'):
      xmlns = ' xmlns:NS="' + kw['ns'] + '"'
      ns = 'NS:'
      del kw['ns']
    else:
      xmlns = ns = ''
    assert not kw, 'unknown arguments'
    body = XML_DOC_HEADER + \
           '<DAV:propertyupdate xmlns:DAV="DAV:"' + xmlns + \
           '><DAV:remove><DAV:prop><' + ns + \
           string.joinfields(names, '/><' + ns) + \
           '/></DAV:prop></DAV:remove></DAV:propertyupdate>'
    return self.proppatch(url, body)

  def setprops(self, url, *xmlprops, **props):
    assert xmlprops or props, 'at least one property must be provided'
    xmlprops = list(xmlprops)
    if props.has_key('ns'):
      xmlns = ' xmlns:NS="' + props['ns'] + '"'
      ns = 'NS:'
      del props['ns']
    else:
      xmlns = ns = ''
    for key, value in props.items():
      if value:
        xmlprops.append('<%s%s>%s</%s%s>' % (ns, key, value, ns, key))
      else:
        xmlprops.append('<%s%s/>' % (ns, key))
    elems = string.joinfields(xmlprops, '')
    body = XML_DOC_HEADER + \
           '<DAV:propertyupdate xmlns:DAV="DAV:"' + xmlns + \
           '><DAV:set><DAV:prop>' + \
           elems + \
           '</DAV:prop></DAV:set></DAV:propertyupdate>'
    return self.proppatch(url, body)


  """ My new and improved? version """
  def setprops2(self, url, xmlstuff):
    body = XML_DOC_HEADER + \
           '<D:propertyupdate xmlns:D="DAV:">' + \
           '<D:set><D:prop>' + xmlstuff + '</D:prop></D:set>' + \
           '</D:propertyupdate>'

    print body

    return self.proppatch(url, body)


  #def get_lock(self, url, owner='', timeout=None, depth=None):
  #  response = self.lock(url, owner, timeout, depth)
  #  #response.parse_lock_response()
  #  return response.locktoken
