#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


import twisted
from twisted.web import server, resource, static, script
from twisted.internet import reactor
from application import schema, Globals
from osaf import pim
from repository.item import Access
import os
import logging
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

def installParcel(parcel, oldVersion=None):
    pim.Principal.update(parcel, 'public',
        displayName=_("Public")
    )


def start_servers(startup_item):
    if getattr(Globals.options,'webserver',False):
        from osaf.startup import run_reactor
        # Start up all webservers
        run_reactor()
        for server in Server.iterItems(startup_item.itsView):
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
        doc="The port to listen on"
    )

    path = schema.One(
        schema.Text,
        doc="The filesystem path pointing to the server's doc root.  This "
            "path is relative to the current working directory, or it can "
            "be absolute"
    )

    resources = schema.Sequence(
        initialValue=(),
        doc = "You may define custom twisted resources and associate them "
              "with this server"
    )

    directories = schema.Sequence(
        initialValue=(),
        doc = "You may specify other file system directories which will be "
              "used to server specific URL locations.  (See the Directory "
              "Kind)"
    )

    def startup(self):
        docRoot = self.path
       
        # Need to convert from unicode to bytes 
        root = static.File(docRoot.encode("UTF-8"))

        # .rpy files are twisted's version of a cgi
        root.ignoreExt(".rpy")
        root.processors = {".rpy" : script.ResourceScript}

        logger.info(u"Activating web server on port %s with docroot %s" % \
         (self.port, docRoot))

        # Hook up all associated resources to a location under the docroot
        for res in self.resources:
            logger.info(u"   Hooking up /%s to resource '%s'" % \
             (res.location, res.itsName))
            resourceInstance = res.getResource()

            # Give the main thread repository view to the resource instance
            resourceInstance.repositoryView = self.itsView

            # Also give the twisted web resource a handle to the resource
            # item
            resourceInstance.resourceItem = res
            root.putChild(res.location, resourceInstance)

        # Hook up all associated directories to a location under the docroot
        for directory in self.directories:
            module = schema.importString(directory.module)
            moduleDir = os.path.dirname(module.__file__)
            docRoot = os.path.join(moduleDir, directory.path)
            logger.info(u"   Hooking up /%s to directory %s" %
                (directory.location, docRoot))
            root.putChild(directory.location, static.File(docRoot))

        site = server.Site(root)
        try:
            reactor.callFromThread(reactor.listenTCP, self.port, site)
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

    location = schema.One(schema.Text)

    server = schema.One(
        Server,
        initialValue=None,
        inverse=Server.resources
    )

    autoView = schema.One(schema.Boolean,
        initialValue=True,
        doc="Resouce should automatically create a private view, refresh() "
            "before rendering, and commit() afterwards"
    )

    resourceClass = schema.One(
        schema.Class,
        initialValue=None)

    def getResource(self):
        return self.resourceClass()


class AuthenticatedResource(resource.Resource):
    """
    A twisted.web.resource (non Chandler item) which provides methods for
    login/password authentication
    """

    def render(self, request):

        session = request.getSession()

        if self.resourceItem.autoView:
            # Create our own view (for this resource) if it doesn't exist
            if not hasattr(self, 'myView'):
                repo = self.repositoryView.repository
                viewName = 'servlet_%s_view' % request.path
                self.myView = repo.createView(viewName)
                ## @@@MOR I wonder if I should have separate repository views
                ## per resource+user; is it dangerous to have different users
                ## share the same view?

            self.myView.refresh()
        else:
            self.myView = self.repositoryView


        args = request.args
        if args.has_key('command'):
            command = args['command'][0]
        else:
            command = None

        # See if the user is trying to log in
        if command == 'login':
            login = args['login'][0]
            password = args['password'][0]
            uuid = self.authenticate(login, password)
            if uuid is not None:
                session.user = uuid
                request.method = 'GET'
                request.args['command'] = ['default']

        elif command == 'logout':
            if hasattr(session, 'user'):
                del session.user
                # We'll get set to 'public' a few lines down...

        # Set user to 'public' if not set to something already
        public = schema.ns('osaf.webserver', self.myView).public.itsUUID
        session.user = getattr(session, 'user', public)
        user = self.resourceItem.itsView.findUUID(session.user)

        acl = self.resourceItem.getACL(default=None)
        if (not acl) or acl.verify(user, Access.Permissions.READ):
            method = getattr(self, 'render_' + request.method, None)
            if not method:
                raise server.Unsupported(getattr(self, 'allowedMethods', ()))

            output = method(request)

            if self.resourceItem.autoView:
                self.myView.commit()

            return output

        else:
            return self.loginPage(request)


    def authenticate(self, login, password):
        """
        Return uuid of User item matching login/password, or None if no match
        """

        for principal in pim.Principal.iterItems(self.resourceItem.itsView):
            if (login == getattr(principal, 'login', '') and
                password == getattr(principal, 'password', '')):
                return principal.itsUUID
        return None


    def loginPage(self, request):
        """
        A generic login page, which you'll probably want to override...
        """

        return """
            <?xml version="1.0" encoding="utf-8"?>
            <html xmlns="http://www.w3.org/1999/xhtml">
              <head>
                <title>Login</title>
              </head>
              <body>
                <h1>Login</h1>
                <form action="%s" method="post">
                Username:<br/>
                <input type="text" name="login" size="20" /><br/>
                Password:<br/>
                <input type="password" name="password" size="20" /><br/>
                <input type="hidden" name="command" value="login" />
                <input type="submit" value="Login" />
                </form>
              </body>
            </html>
        """ % request.path

class Directory(schema.Item):
    """
         The web directory Kind.  Defining instances of Directory, and
         associating them with a server is a way to "graft" a different
         file system directory into the server's document tree.  For example
         if you want HTTP requests for the /images/ location to not be
         served from the server's docroot/images directory, but rather from
         some other directory, you can define a Directory item with location
         of "/images" and path of relativepath/to/your/images/ and set its
         server attribute to a web server item.
    """

    location = schema.One(schema.Text)

    path = schema.One(schema.Text,)

    module = schema.One(schema.Text,
        doc = "In order to find the filesystem directory to associate with "
              "this Directory resource, we need to know the python module "
              "(dotted name) the resource came from. Set it in this attribute. "
              "The filesystem directory the module lives in will be determined "
              "and then the 'path' attribute is relative to that directory."
    )

    server = schema.One(
        Server,
        initialValue=None,
        inverse=Server.directories
    )
