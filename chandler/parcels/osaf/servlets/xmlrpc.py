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


from application import schema
from osaf import webserver, pim
import sys, traceback
from twisted.web import xmlrpc
from util import commandline

# For current( )
from osaf.framework import blocks

def setattr_withtype(item, attribute, stringValue):
    """
    A wrapper around setattr which correctly unserializes a string
    value into an appropriate attribute value
    """
    v = item.getAttributeAspect(attribute, 'type').makeValue(stringValue)
    return setattr(item, attribute, v)


def getServletView(repository, name=None):

    if name is None:
        name = "XMLRPC"

    for existingView in repository.views:
        if existingView.name == name:
            return existingView

    return repository.createView(name)


class XmlRpcResource(xmlrpc.XMLRPC):

    def render(self, request):
        'Only allow XML-RPC connections from localhost'

        if request.getClientIP() == '127.0.0.1':
            return xmlrpc.XMLRPC.render(self, request)
        else:
            return xmlrpc.Fault(self.FAILURE, "Not localhost")

    def xmlrpc_echo(self, text):
        return "I received: '%s'" % text

    def xmlrpc_current(self):
        view = self.repositoryView
        item = None
        for block in blocks.detail.DetailRootBlock.iterItems(view=view):
            if hasattr(block, 'widget'):
                item = getattr(block, 'contents', None)
                break

        if item is not None:
            result = item.displayName
        else:
            result = "nothing selected"

        return result

    def xmlrpc_commandline(self, text, viewName=None):
        view = getServletView(self.repositoryView.repository, viewName)
        view.refresh()
        commandline.execute_command(view, text)
        view.commit()
        return "OK" # ???

    def xmlrpc_note(self, title, body, viewName=None):
        view = getServletView(self.repositoryView.repository, viewName)
        view.refresh()
        note = pim.Note(itsView=view)
        note.body = note.getAttributeAspect('body', 'type').makeValue(body,
            indexed=True)
        view.commit()
        return "OK" # ???


    #
    # Generic repository API
    #
    def generic_item_call(self, viewName, method, objectPath, *args, **kwds):
        view = getServletView(self.repositoryView.repository, viewName)
        view.refresh()

        try:
            item = view.findPath(objectPath)
            result = method(item, *args, **kwds)
        except Exception, e:
            print "error in generic_item_call: %s" % e
            raise

        # ugh, XML-RPC doesn't like None as a result
        if result is None:
            return True
        return result

    def xmlrpc_setAttribute(self, objectPath, attrName, value, viewName=None):
        """
        generic setAttribute - assumes the value is a atomic value -
        i.e. a string or an integer or something
        """
        return self.generic_item_call(viewName, setattr_withtype, objectPath, attrName, value)

    def xmlrpc_getAttribute(self, objectPath, attrName, value, viewName=None):
        """
        generic getAttribute - assumes the resulting value will be an
        atomic value like a string or an integer
        """
        return self.generic_item_call(viewName, getattr, objectPath, attrName, value)

    def xmlrpc_delAttribute(self, objectPath, attrName, viewName=None):
        """
        removes an attribute from an object
        """
        return self.generic_item_call(viewName, delattr, objectPath, attrName)

    def xmlrpc_commit(self, viewName=None):
        """
        commits the xml-rpc view
        """
        view = getServletView(self.repositoryView.repository, viewName)
        view.commit()
        return True
