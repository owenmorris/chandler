import twisted
from twisted.web import server, resource, static, script
from twisted.internet import reactor
import application
from application import schema, Globals
from osaf import pim
from repository.item.Item import Item
from repository.util.ClassLoader import ClassLoader
import os, sys
import logging
from i18n import OSAFMessageFactory as _

logger = logging.getLogger(__name__)

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
        displayName=_(u"Port"),
        doc="The port to listen on"
    )

    path = schema.One(
        schema.Text,
        displayName=_(u"Path"),
        doc="The filesystem path pointing to the server's doc root.  This "
            "path is relative to the current working directory, or it can "
            "be absolute"
    )

    resources = schema.Sequence(
        initialValue=(),
        displayName=_(u"Resources"),
        doc = "You may define custom twisted resources and associate them "
              "with this server"
    )

    directories = schema.Sequence(
        initialValue=(),
        displayName=_(u"Directories"),
        doc = "You may specify other file system directories which will be "
              "used to server specific URL locations.  (See the Directory "
              "Kind)"
    )

    def startup(self):
        docRoot = self.path
        root = static.File(docRoot)

        # .rpy files are twisted's version of a cgi
        root.ignoreExt(".rpy")
        root.processors = {".rpy" : script.ResourceScript}

        logger.info(u"Activating web server on port %s with docroot %s" % \
         (self.port, docRoot))

        # Hook up all associated resources to a location under the docroot
        for res in self.resources:
            logger.info(u"   Hooking up /%s to resource '%s'" % \
             (res.location, res.displayName))
            resourceInstance = res.getResource()

            # Give the main thread repository view to the resource instance
            resourceInstance.repositoryView = self.itsView

            # Also give the twisted web resource a handle to the resource
            # item
            resourceInstance.resourceItem = res
            root.putChild(res.location, resourceInstance)

        # Hook up all associated directories to a location under the docroot
        for directory in self.directories:
            # First, find this directory's parcel, then determine that parcel's
            # directory, then join the directory.path.
            parcel = application.Parcel.Manager.getParentParcel(directory)
            parcelDir = os.path.dirname(parcel.file)
            docRoot = os.path.join(parcelDir, directory.path)
            logger.info(u"   Hooking up /%s to directory %s" % \
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

    location = schema.One(schema.Text, displayName=_(u"Location"))

    server = schema.One(
        Server,
        displayName=_(u"Server"),
        initialValue=None,
        inverse=Server.resources
    )

    users = schema.Sequence("User", inverse='resources',
        doc="A ref collection of users who have access to this resource"
    )

    autoView = schema.One(schema.Boolean,
        initialValue=True,
        doc="Resouce should automatically create a private view, refresh() "
            "before rendering, and commit() afterwards"
    )

    resourceClass = schema.One(
        schema.Class,
        displayName=u"Resource Class",
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

        users = getattr(self.resourceItem, 'users', None)

        args = request.args
        if args.has_key('command'):
            command = args['command'][0]

            if users is not None:

                if command == 'login':
                    login = request.args['login'][0]
                    password = request.args['password'][0]
                    session.user = self.authenticate(login, password)
                    request.method = 'GET'
                    request.args['command'] = ['default']

                elif command == 'logout':
                    if hasattr(session, 'user'):
                        del session.user
                    return self.loginPage(request)


        if users is None:
            userAllowed = True
        else:
            userAllowed = False
            if getattr(session, 'user', None) is not None:
                userItem = self.resourceItem.itsView.findUUID(session.user)
                if userItem in self.resourceItem.users:
                    userAllowed = True

        if userAllowed:
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

        for user in self.resourceItem.users:
            if login == user.login and password == user.password:
                return user.itsUUID
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
         of "/images" and path of /path/to/your/images/ and set its server
         attribute to a web server item.
    """

    location = schema.One(schema.Text, displayName=_(u"Location"))

    path = schema.One(schema.Text, displayName=_(u"Path"))

    server = schema.One(
        Server,
        displayName=_(u"Server"),
        initialValue=None,
        inverse=Server.directories
    )

class User(pim.ContentItem):
    login = schema.One(schema.Text)
    password = schema.One(schema.Text)
    resources = schema.Sequence(Resource, inverse='users')

