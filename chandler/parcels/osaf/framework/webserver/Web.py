__parcel__ = "osaf.framework.webserver"
import twisted
from twisted.web import server, resource, static, script
from twisted.internet import reactor
import application
import application.Globals as Globals
from application import schema
from repository.item.Item import Item
from repository.util.ClassLoader import ClassLoader
import os, sys
import logging

logger = logging.getLogger('WebServer')
logger.setLevel(logging.INFO)

class WebParcel(application.Parcel.Parcel):
    def startupParcel(self):
        super(WebParcel, self).startupParcel()
        activate = False
        try:
            if Globals.options.webserver:
                activate = True
        except:
            pass

        if activate:
            # Start up all webservers
            for server in Server.iterItems(self.itsView):
                server.startup()

class Server(schema.Item):
    """
         The web server Kind.  Instances of this Kind are found via KindQuery
         at startup and activated.  You may define a server item in your own
         parcel, and it will run as well as the default one defined in the
         webserver/servers parcel.
    """

    port = schema.One(
        schema.Integer,
        displayName="Port",
        doc="The port to listen on"
    )

    path = schema.One(
        schema.String,
        displayName="Path",
        doc="The filesystem path pointing to the server's doc root.  This "
            "path is relative to the directory of the parcel.xml that "
            "defines the server item"
    )

    resources = schema.Sequence(
        initialValue=(),
        displayName="Resources",
        doc = "You may define custom twisted resources and associate them "
              "with this server"
    )

    directories = schema.Sequence(
        initialValue=(),
        displayName="Directories",
        doc = "You may specify other file system directories which will be "
              "used to server specific URL locations.  (See the Directory "
              "Kind)"
    )

    def startup(self):
        parcel = application.Parcel.Manager.getParentParcel(self)
        parcelDir = os.path.dirname(parcel.file)
        docRoot = os.path.join(parcelDir, self.path)
        root = static.File(docRoot)

        # .rpy files are twisted's version of a cgi
        root.ignoreExt(".rpy")
        root.processors = {".rpy" : script.ResourceScript}

        logger.info("Activating web server on port %s with docroot %s" % \
         (str(self.port), str(docRoot)))

        # Hook up all associated resources to a location under the docroot
        for res in self.resources:
            logger.info("   Hooking up /%s to resource '%s'" % \
             (str(res.location), str(res.displayName)))
            resourceInstance = res.getResource()
            # Give the main thread repository view to the resource instance
            resourceInstance.repositoryView = self.itsView
            root.putChild(res.location, resourceInstance)

        # Hook up all associated directories to a location under the docroot
        for directory in self.directories:
            # First, find this directory's parcel, then determine that parcel's
            # directory, then join the directory.path.
            parcel = application.Parcel.Manager.getParentParcel(directory)
            parcelDir = os.path.dirname(parcel.file)
            docRoot = os.path.join(parcelDir, directory.path)
            logger.info("   Hooking up /%s to directory %s" % \
             (str(directory.location), str(docRoot)))
            root.putChild(directory.location, static.File(docRoot))

        site = server.Site(root)
        try:
            reactor.listenTCP(self.port, site)
            self.activated = True
        except twisted.internet.error.CannotListenError, e:
            logger.error("Twisted error: %s" % str(e))
            print e

    def isActivated(self):
        return (hasattr(self, 'activated') and self.activated)

class Resource(schema.Item):
    """
         The web resource Kind.  Resources are a twisted.web concept (see
         "Resource Objects" within this page:
         http://www.twistedmatrix.com/documents/current/howto/using-twistedweb
         ).  A resource is a python class which handles HTTP requests and
         returns an HTML string.  For example, if you want your web server
         to send all HTTP requests for the location /xyzzy to be handled
         by a custom resource, define a resource item, set its location
         attribute to "/xyzzy", its resourceClass to "yourpackage.yourmodule.
         yourresource", and assign the server attribute to the desired
         server.
    """

    location = schema.One(schema.String, displayName="Location")

    server = schema.One(
        Server,
        displayName="Server",
        initialValue=None,
        inverse=Server.resources
    )

    resourceClass = schema.One(
        schema.Class,
        displayName="Resource Class",
        initialValue=None)

    def getResource(self):
        return self.resourceClass()


class Directory(schema.Item):
    """
         The web directory Kind.  Defining instances of Directory, and
         associating them with a server is a way to "graft" a different
         file system directory into the server's document tree.  For example
         if you want HTTP requests for the /images/ location to not be
         served from the server's docroot/images directory, but rather from
         some other directory, you can define a Directory item with location
         of "/images" and path of /path/to/your/images/ and set its server
         attribute to a web server item.
    """

    location = schema.One(schema.String, displayName="Location")

    path = schema.One(schema.String, displayName="Path")

    server = schema.One(
        Server,
        displayName="Server",
        initialValue=None,
        inverse=Server.directories
    )
