__parcel__ = "osaf.framework.webserver"
import twisted
from twisted.web import server, resource, static, script
from twisted.internet import reactor
import application
import application.Globals as Globals
from application import schema
from repository.item.Item import Item
from repository.item.Query import KindQuery
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
            serverKind = self.lookup("Server")
            for server in KindQuery().run([serverKind]):
                server.startup()

class Server(schema.Item):
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
        except twisted.internet.error.CannotListenError, e:
            logger.error("Twisted error: %s" % str(e))
            print e

class Resource(schema.Item):
    def getResource(self):
        return self.resourceClass()
