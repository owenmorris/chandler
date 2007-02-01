#   Copyright (c) 2006-2007 Open Source Applications Foundation
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

import davclient
import copy

from xml.etree import ElementTree

def dict_to_elem(parent, dict_vals, namespace=None):
    for key, value in dict_vals.items():
        if namespace is None:
            element = ElementTree.SubElement(parent, key)
        else:
            element = ElementTree.SubElement(parent, '{'+namespace+'}'+key)
        element.text = value

class CosmoClient(davclient.DAVClient):
    """Class for adding cosmo specific functionality to DAVClient"""
    
    _cosmo_path = '/cosmo/'
    _cmp_path = _cosmo_path+'cmp'
    
    def set_cmp_path(self, path):
        _cmp_path = path
        
    def set_cosmo_path(self, path):
        _cosmo_path = path
        
    def add_user(self, username, password, first_name, last_name, email, request_method=None):
        if request_method is None:
            request_method = self.put 
        
        root = ElementTree.Element('{http://osafoundation.org/cosmo/CMP}user')
        vals = {'username':username, 'password':password, 'firstName':first_name, 'lastName':last_name, 'email':email}
        dict_to_elem(root, vals, namespace='http://osafoundation.org/cosmo/CMP')
        request_method(self._cmp_path+'/user/%s'%username, body=unicode(ElementTree.tostring(root), 'utf-8'),
                       headers={'content-type': 'text/xml; charset=utf-8'})
        
    def modify_user(self, user_dict, request_method=None):
        if request_method is None:
            request_method = self.put
            
        root = ElementTree.Element('{http://osafoundation.org/cosmo/CMP}user')
        dict_to_elem(root, user_dict, namespace='http://osafoundation.org/cosmo/CMP')
        print unicode(ElementTree.tostring(root), 'utf-8')
        request_method(self._cmp_path+'/user/%s'%user_dict['username'], body=unicode(ElementTree.tostring(root), 'utf-8'), headers={'content-type': 'text/xml; charset=utf-8'})
        
    def mkcalendar(self, username=None):
        if username is None:
            username = self._username
            
        self._request()
        
    def remove_user(self, user):
        self.delete(self._cmp_path+'/user/%s' % user)
        
    def get_users(self, headers=None):
        
        self._request('GET', self._cmp_path+'/users', body=None, headers=headers)
        elements = self.response.tree.findall('.//{http://osafoundation.org/cosmo/CMP}username')
        self._users = []
        for element in elements:
            self._users.append(element.text)
        return self._users
    
    def get_all_events(self, user, collection='/'):
        """Get all the events for a given user. Returns list of dict objects with 'href' and 'body'"""
        self.propfind(self._cosmo_path+'home/'+user+collection)
        hrefs = self.response.tree.findall('//{DAV:}href')
        events = []
        for ref in hrefs:
            if ref.text.endswith('.ics'):
                event = {'href':ref.text}
                print ref.text.replace(self._url.geturl(), '')
                self.get(ref.text.replace(self._url.geturl(), ''))
                event['body'] = copy.copy(self.response.body)
                events.append(event)
        return events
        
    def get_all_users_events(self):
        """Get all the events for all users on the server. Returns dict object where key is username and value is list of event dict object from CosmoClient.get_all_events"""
        if not hasattr(self, '_users'):
            self.get_users()
        
        all_events = {}
        for user in self._users:
            print 'Getting all events for user "%s"' % user
            events = self.get_all_events(user)
            all_events[user] = events
            
        return all_events