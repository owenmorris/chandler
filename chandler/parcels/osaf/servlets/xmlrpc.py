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

view = None

def getServletView(repository):
    global view
    if view is None:
        view = repository.createView("XMLRPC")
    return view

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

    def xmlrpc_commandline(self, text):
        view = getServletView(self.repositoryView.repository)
        view.refresh()
        commandline.execute_command(view, text)
        view.commit()
        return "OK" # ???

    def xmlrpc_note(self, title, body):
        view = getServletView(self.repositoryView.repository)
        view.refresh()
        note = pim.Note(itsView=view, displayName=title)
        note.body = note.getAttributeAspect('body', 'type').makeValue(body,
            indexed=True)
        view.commit()
        return "OK" # ???


    #
    # Generic repository API
    #
    def generic_item_call(self, method, objectPath, *args, **kwds):
        view = getServletView(self.repositoryView.repository)
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

    def xmlrpc_setAttribute(self, objectPath, attrName, value):
        """
        generic setAttribute - assumes the value is a atomic value -
        i.e. a string or an integer or something
        """
        return self.generic_item_call(setattr_withtype, objectPath, attrName, value)

    def xmlrpc_getAttribute(self, objectPath, attrName, value):
        """
        generic getAttribute - assumes the resulting value will be an
        atomic value like a string or an integer
        """
        return self.generic_item_call(getattr, objectPath, attrName, value)

    def xmlrpc_delAttribute(self, objectPath, attrName):
        """
        removes an attribute from an object
        """
        return self.generic_item_call(delattr, objectPath, attrName)

    def xmlrpc_commit(self):
        """
        commits the xml-rpc view
        """
        view = getServletView(self.repositoryView.repository)
        view.commit()
        return True
