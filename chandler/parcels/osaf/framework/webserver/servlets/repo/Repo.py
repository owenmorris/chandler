import os, sys, string, traceback

from twisted.web import resource
# import application.Globals as Globals
import repository
import application
import re
from osaf.contentmodel.ContentModel import ContentItem
from repository.item.Item import Item
from repository.schema.Kind import Kind
from repository.schema.Types import Type
from repository.schema.TypeHandler import TypeHandler
from repository.util.Lob import Lob
from repository.util.URL import URL
from repository.schema.Attribute import Attribute
from repository.schema.Cloud import Cloud, Endpoint
from repository.item.RefCollections import RefList
from repository.util.SingleRef import SingleRef


class RepoResource(resource.Resource):
    isLeaf = True
    def render_GET(self, request):

        cookies = request.received_cookies
        
        try: # Outer try to render any exceptions

            try: # Inner try/finally to handle restoration of current view

                mode = request.args.get('mode', [None])[0]
                
                # First check args, then check cookie for view to use:
                viewName = request.args.get('view', [cookies.get('view', None)])[0]

                # The Server item will give us the repositoryView during
                # startup.  Set it to be the current view and restore the
                # previous view when we're done.
                repoView = self.repositoryView
                
                # See if we need to override, using a different view
                if viewName:
                    for view in repoView.views:
                        if view.name == viewName:
                            repoView = view
                            break
                        
                request.addCookie("view", repoView.name, path="/repo")
                
                prevView = repoView.setCurrentView()

                if not request.postpath or not request.postpath[0]:
                    path = "//"
                else:
                    path = "//%s" % ("/".join(request.postpath))
                    
                result = "<html><head><title>Chandler : %s</title><link rel='stylesheet' href='/site.css' type='text/css' /></head>" % request.path
                result += "<body>"

                
                result += "<p class=footer>Repository view: <b>%s</b> | <a href=/repo/?mode=views>switch</a></p>" % repoView.name
                
                if mode == "kindquery":
                    item = repoView.findPath(path)
                    result += "<div>"
                    result += RenderKindQuery(repoView, item)
                    result += "</div>"

                elif mode == "views":
                    result = RenderViews(repoView)
                    
                elif mode == "search":
                    text = request.args.get('text', [None])[0]
                    result += RenderSearchResults(repoView, text)

                elif mode == "blocks":
                    item = repoView.findPath(path)
                    path = "<a href=%s>[top]</a>" % toLink("/")
                    i = 2
                    for part in item.itsPath[1:-1]:
                        path += " &gt; <a href=%s>%s</a>" % (toLink(item.itsPath[:i]), part)
                        i += 1

                    name = item.itsName
                    if name is None:
                        name = str(item.itsUUID)
                    result += "<div class='path'>%s &gt; <span class='itemname'><a href=%s>%s</a></span> | <a href=%s>Render attributes</a></div>" % (path, toLink(item.itsPath), name, toLink(item.itsPath))

                    result += RenderBlock(repoView, item)

                elif mode == "object":
                    fields = []
                    item = None
                    itemPath = path
                    # The path is like: //path/to/item/field/field
                    # Separate out the fields until we find the item.
                    while True:
                        item = repoView.findPath(itemPath)
                        if item is None:
                            lastSlash = itemPath.rfind('/')
                            if (lastSlash == -1):
                                break;
                            field = itemPath[(lastSlash + 1):]
                            fields.insert(0, field)
                            itemPath = itemPath[:lastSlash]
                        else:
                            break
                        
                    if item is None:
                        result += "<h3>Item not found: %s</h3>" % clean(path)
                        return str(result)

                    if len(fields) == 0:
                        # No fields - just go render the item.
                        return RenderItem(repoView, item)
                    
                    # Drill down to the field we want
                    theValue = item
                    for f in fields:
                        try:
                            theValue = _getObjectValue(theValue, f)
                        except:
                            result += "<h3>Unable to get %s on %s</h3>" % (clean(f), clean(theValue))
                            return str(result)
                    result += "<div>"
                    result += RenderObject(repoView, theValue, path)
                    result += "</div>"

                elif mode == "inheritance":
                    result += RenderInheritance(repoView)

                elif path != "//":
                    item = repoView.findPath(path)
                    if item is None:
                        result += "<h3>Item not found: %s</h3>" % path
                        return str(result)

                    result += "<div>"
                    result += RenderItem(repoView, item)
                    result += "</div>"
                else:
                    result += RenderSearchForm(repoView)
                    result += "<p>"
                    result += RenderRoots(repoView)
                    result += "<p>"
                    result += RenderKinds(repoView)
                    result += "<p>"
                    result += RenderAllClouds(repoView)

            finally: # inner try
                if prevView:
                    prevView.setCurrentView()

        except Exception, e: # outer try
            result = "<html>Caught a %s exception: %s<br> %s</html>" % (type(e), e, "<br>".join(traceback.format_tb(sys.exc_traceback)))

        if isinstance(result, unicode):
            result = result.encode('ascii', 'replace')
            
        return result


def RenderSearchForm(repoView):
    result = ""
    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>PyLucene Search:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td>"
    result += "<div class='tree'>"
    result += "<form method=get action=/repo><input type=text name=text size=40><input type=hidden name=mode value=search>"
    result += "</div>"
    result += "</td></tr></table></form>\n"
    return result

def RenderSearchResults(repoView, text):
    result = ""
    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>PyLucene Search Results for <i>%s</i> :</b></td>\n" % text
    result += "</tr>\n"
    count = 0
    for (item, attribute) in repoView.searchItems(text):
        result += oddEvenRow(count)
        result += "<td><a href=%s>%s</a></td>" % (toLink(item.itsPath), item.getItemDisplayName())
        result += "</tr>"
        count += 1
    result += "</table></form>\n"
    return result

def RenderRoots(repoView):
    result = ""
    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>Repository Roots:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td>"
    result += "<div class='tree'>"
    for child in repoView.iterRoots():
        result += "<a href=%s>//%s</a> &nbsp;  " % (toLink(child.itsPath), child.itsName)
    result += "</div>"
    result += "</td></tr></table>\n"
    return result

def RenderViews(repoView):
    result = ""
    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>Repository Views:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td>"
    result += "<div class='tree'>"
    for view in repoView.views:
        if repoView == view:
            result += "<b>%s</b> &nbsp;  " % (view.name)
        else:
            result += "<a href=/repo/?view=%s>%s</a> &nbsp;  " % (view.name, view.name)
    result += "</div>"
    result += "</td></tr></table>\n"
    return result

def RenderInheritance(repoView):
    result = ""
    kinds = []
    for item in repository.item.Query.KindQuery().run(
     [
      repoView.findPath("//Schema/Core/Kind"),
     ]
    ):
        kinds.append(item)

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td colspan=5><b>All Kinds:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td><b>Kind</b></td><td><b>Class</b></td><td><b>myKindPath</b></td><td><b>Superclasses</b></td><td><b>Superkinds</b></td>\n"
    result += "</tr>\n"

    count = 0
    for item in kinds:
        result += oddEvenRow(count)
        result += "<td><a href=%s>%s</a></td>" % (toLink(item.itsPath), item.getItemDisplayName())
        result += "<td>"
        klass = None
        if hasattr(item, 'classes'):
            klass = item.classes['python']
            result += clean(str(klass))
        result += "</td>"
        result += "<td>"
        if klass is not None:
            if hasattr(klass, 'getKind'):
                checkKind = klass.getKind(repoView)
                result += str(checkKind.itsPath)
                if checkKind is item:
                    result += " (ok)"
                else:
                    result += " <b>(MISMATCH)</b>"
        result += "</td>"
        result += "<td>"
        if klass is not None:
            for superclass in klass.__bases__:
                result += clean(str(superclass)) + ", "
        result += "</td>"

        result += "<td>"
        for superKind in item.superKinds:
            result += superKind.getItemDisplayName() + ", "
        result += "</td>"
        result += "</tr>"
        count += 1
    result += "</table>\n"

    return result

def RenderKinds(repoView):
    result = ""
    items = {}
    tree = {}
    for item in repository.item.Query.KindQuery().run(
     [
      repoView.findPath("//Schema/Core/Kind"),
     ]
    ):
        items[item.itsPath] = item
        _insertItem(tree, item.itsPath[1:], item)

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>All Kinds:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td>"
    result += "<div class='tree'>"
    result += _RenderNode(repoView, tree)
    result += "</div>"
    result += "</td></tr></table>\n"

    return result

def _insertItem(node, path, item):
    top = str(path[0])
    rest = path[1:]
    if not node.has_key(top):
        node[top] = {}

    if not rest:
        node[top][""] = item
        return
    _insertItem(node[top], rest, item)



def _RenderNode(repoView, node, depth=1):
    result = ""

    keys = node.keys()
    keys.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
    output = []
    for key in keys:
        if key == "":
            continue
        if node[key].has_key(""):
            # for d in range(depth):
            #     result += "&nbsp;&nbsp;&nbsp;"
            item = node[key][""]
            output.append("<a href=%s>%s</a>" % (toLink(item.itsPath), 
             item.itsName))
    if output:
        result += ": "
    result += (", ".join(output))
    result += "\n"
    for key in keys:
        if key == "":
            continue
        if not node[key].has_key(""):
            result += "<ul>"
            # for d in range(depth):
            #     result += "&nbsp;&nbsp;&nbsp;"
            result += "<li>"
            result += "<b>%s</b>" % key
            result += _RenderNode(repoView, node[key], depth+1)
            result += "</ul>"

    return result


def _getAllClouds(kind):
    """ A generator which returns every cloud for a given kind.  """

    clouds = kind.getAttributeValue('clouds', default=None)
    if clouds:
        for cloud in clouds:
            yield (cloud, cloud.kind.clouds.getAlias(cloud))

    superKinds = kind.getAttributeValue('superKinds', default=None)
    if superKinds:
        for superKind in superKinds:
            for (cloud, alias) in _getAllClouds(superKind):
                yield (cloud, alias)


def RenderAllClouds(repoView):
    result = ""

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>All Clouds:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td>"
    result += "<div class='tree'>"

    clouds = {}
    for cloud in repository.item.Query.KindQuery().run([repoView.findPath("//Schema/Core/Cloud")]):
        clouds[cloud.itsPath] = cloud
    keys = clouds.keys()
    keys.sort()
    for key in keys:
        cloud = clouds[key]
        result += "<p>"
        result += "Cloud <a href=%s>%s</a> for kind <a href=%s>%s</a>" % \
         (toLink(cloud.itsPath), cloud.itsPath, toLink(cloud.kind.itsPath), 
         cloud.kind.itsName)
        alias = cloud.kind.clouds.getAlias(cloud)
        if alias:
            result += " (alias '%s')" % alias
        result += "<br>"
        for endpoint in cloud.endpoints:
            result += "&nbsp;&nbsp;&nbsp;Endpoint <a href=%s>%s</a>:" % (toLink(endpoint.itsPath), endpoint.itsName)
            result += " attribute '"
            result += (".".join(endpoint.attribute))
            result += "', "
            alias = cloud.endpoints.getAlias(endpoint)
            if alias:
                result += " (alias '%s')" % alias
            result += " policy '%s'" % endpoint.includePolicy
            if endpoint.includePolicy == "byCloud":
                if endpoint.getAttributeValue('cloud', default=None) is not \
                 None:
                    result += " --&gt; <a href=%s>%s</a>" % (toLink(endpoint.cloud.itsPath), endpoint.cloud.itsName)
                elif endpoint.getAttributeValue('cloudAlias', default=None) \
                 is not None:
                    result += " to cloud alias '%s'" % endpoint.cloudAlias

            result += "<br>"
        result += "</p>"

    result += "</div>"
    result += "</td></tr></table>\n"

    return result


def RenderClouds(repoView, kind):
    """ Given a kind, return a representation of the default cloud """

    result = ""

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td colspan=2><b>Clouds associated with this kind:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='headingsrow'>\n"
    result += "<td valign=top><b>Cloud</b></td>\n"
    result += "<td valign=top><b>Endpoints</b></td>\n"
    result += "</tr>\n"

    # Retreive all cloud aliases
    cloudAliases = {}
    for (cloud, cloudAlias) in _getAllClouds(kind):
        cloudAliases[cloudAlias] = cloud

    count = 0
    for cloudAlias in cloudAliases.keys():
        result += oddEvenRow(count)
        result += "<td valign=top>%s</td>\n" % cloudAlias
        result += "<td valign=top>"
        cloud = kind.getClouds(cloudAlias=cloudAlias)[0]
        for (alias, endpoint, foundInCloud) in \
         cloud.iterEndpoints(cloudAlias=cloudAlias):
            result += "<a href=%s>%s</a> in cloud %s: " % (toLink(endpoint.itsPath), endpoint.itsName, foundInCloud.itsPath)
            if alias:
                result += " (alias '%s')" % alias
            result += " policy '%s'" % endpoint.includePolicy
            if endpoint.includePolicy == "byCloud":
                if endpoint.getAttributeValue('cloud', default=None) is not \
                 None:
                    result += " --&gt; <a href=%s>%s</a>" % (toLink(endpoint.cloud.itsPath), endpoint.cloud.itsName)
                elif endpoint.getAttributeValue('cloudAlias', default=None) \
                 is not None:
                    result += " to cloud alias '%s'" % endpoint.cloudAlias
            result += "<br>\n"
        result += "</td></tr>\n"
        count += 1
    result += "</table>\n"
    return result


def RenderCloudItems(repoView, rootItem):
    """ Given an item, for each related cloud, show all items that belong
        to the cloud. """

    result = ""

    kind = rootItem.itsKind

    # Retreive all cloud aliases
    cloudAliases = {}
    for (cloud, cloudAlias) in _getAllClouds(kind):
        cloudAliases[cloudAlias] = cloud

    for cloudAlias in cloudAliases.keys():
        result += "&nbsp;&nbsp;&nbsp;Cloud '%s': " % cloudAlias
        cloud = kind.getClouds(cloudAlias=cloudAlias)[0]
        output = []
        references = {}
        for item in cloud.getItems(rootItem, references=references, 
         cloudAlias=cloudAlias):
            output.append("<a href=%s>%s</a>" % \
            (toLink(item.itsPath), item.itsName))
        result += (", ".join(output))
        result += " (References included: "
        output = []
        for ref in references.itervalues():
            output.append("<a href=%s>%s</a>" % \
             (toLink(ref.itsPath), ref.itsName))
        result += (", ".join(output))
        result += ")"
        result += "<br>"

    return result

def RenderKindQuery(repoView, item):

    result = ""

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>All Items of Kind: </b>"

    i = 1
    for part in item.itsPath:
        if i > 2: part = "/%s" % part
        result += "<a href=%s>%s</a>" % (toLink(item.itsPath[:i]), part)
        i += 1

    result += "</td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td>"
    result += "<div class='tree'>"

    output = []
    try:
        for i in repository.item.Query.KindQuery().run([item]):
            output.append("<a href=%s>'%s'</a>  (%s) %s %s" % \
                          (toLink(i.itsPath), i.getItemDisplayName(), 
                           i.itsKind.itsName, i.itsPath, 
                           hasattr(i, 'widget') and " (rendered)" or ""))
        result += ("<br>".join(output))
    except Exception, e:
        result += "Caught a %s exception: %s<br> %s" % (type(e), e, "<br>".join(traceback.format_tb(sys.exc_traceback)))
    result += "</div>"
    result += "</td></tr></table>\n"
    return result

def RenderBlock(repoView, block):

    if block.hasLocalAttributeValue('blockName'):
        name = block.blockName
    else:
        name = "[no block name]"

    if block.childrenBlocks.refCount(False) == 0:
        hasChildren = False
    else:
        hasChildren = True

    result = ""
    if hasChildren:
        result += "<table class=block width=100%%>"
    else:
        result += "<table class=childlessblock width=100%%>"
    result += "<tr class=block><td class=block valign=top><a href=%s?mode=blocks>%s</a><a href=%s>.</a></td></tr>" % (toLink(block.itsPath), name, toLink(block.itsPath))

    if block.itsKind.itsName.lower().endswith('bar'):
        mode = 'horizontal'
    else:
        mode = 'vertical'

    try:
        if block.orientationEnum == "Horizontal":
            mode = 'horizontal'
    except:
        pass

    if mode == 'horizontal':
        result += "<tr class=block>"

    for child in block.childrenBlocks:
        childRender = RenderBlock(repoView, child)
        if mode == 'horizontal':
            result += "<td class=block valign=top >%s</td>" % childRender
        else:
            result += "<tr class=block><td class=block width=100%%>%s</td></tr>" % childRender

    if mode == 'horizontal':
        result += "</tr>"

    result += "</table>"
    return result


def RenderItem(repoView, item):

    result = ""

    # For Kinds, display their attributes (except for the internal ones
    # like notFoundAttributes):
    isKind = item.isItemOf(repoView.findPath("//Schema/Core/Kind"))

    isBlock = item.isItemOf(repoView.findPath("//parcels/osaf/framework/blocks/Block"))

    path = "<a href=%s>[top]</a>" % toLink("/")
    i = 2
    for part in item.itsPath[1:-1]:
        path += " &gt; <a href=%s>%s</a>" % (toLink(item.itsPath[:i]), part)
        i += 1

    name = item.itsName
    if name is None:
        name = str(item.itsUUID)
    result += "<div class='path'>%s &gt; <span class='itemname'>%s</span>" % (path, name)

    try: result += " (<a href=%s>%s</a>)" % (toLink(item.itsKind.itsPath), item.itsKind.itsName)
    except: pass

    if isKind:
        result += " | Run a <a href=%s?mode=kindquery>Kind Query</a>" % toLink(item.itsPath)

    if isBlock:
        result += " | <a href=%s?mode=blocks>Render block tree</a>" % toLink(item.itsPath)

    result += "</div>\n"

    try:
        displayName = item.displayName
        result += "<div class='subheader'><b>Display Name:</b> %s</div>\n" % displayName
    except:
        pass

    try:
        description = item.description
        result += "<div class='subheader'><b>Description:</b> %s</div>\n" % description
    except:
        pass

    try:
        issues = item.issues
        result += "<div class='subheader'><b>Issues:</b>\n<ul></div>\n"
        for issue in issues:
            result += "<li>%s\n" % issue
        result += "</ul></p>\n"
    except: pass

    result += "<div class='children'><b>Child items:</b><br> "
    children = {}
    for child in item.iterChildren():
        name = child.itsName
        if name is None:
            name = str(child.itsUUID)
        children[name] = child
    keys = children.keys()
    keys.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
    output = []
    for key in keys:
        child = children[key]
        name = child.itsName
        displayName = ""
        if name is None:
            name = str(child.itsUUID)
            displayName = child.getItemDisplayName()
        children[name] = child
        output.append(" &nbsp; <a href=%s>%s </a> %s" % (toLink(child.itsPath), key, displayName))
    if not output:
        result += " &nbsp; None"
    else:
        result += ("<br>".join(output))
    result += "</div>\n"


    if isKind:
        result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
        result += "<tr class='toprow'>"
        result += "<td colspan=7><b>Attributes defined for this kind:</b></td>"
        result += "</tr>\n"

        result += "<tr class='headingsrow'>\n"
        result += "<td valign=top><b>Attribute</b> (inherited from)</td>\n"
        result += "<td valign=top><b>Description / Issues</b></td>\n"
        result += "<td valign=top><b>Cardinality</b></td>\n"
        result += "<td valign=top><b>Type</b></td>\n"
        result += "<td valign=top><b>Initial&nbsp;Value</b></td>\n"
        # result += "<td valign=top><b>Required?</b></td>\n"
        result += "<td valign=top><b>RedirectTo</b></td>\n"
        result += "</tr>\n"
        count = 0
        displayedAttrs = { }
        for name, attr, kind in item.iterAttributes():
            if name is None: name = "Anonymous"
            displayedAttrs[name] = (attr, kind)
        keys = displayedAttrs.keys()
        keys.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
        for key in keys:
            attribute, kind = displayedAttrs[key]
            result += oddEvenRow(count)
            other = attribute.getAttributeValue('otherName', default="")
            if other: other = " (inverse: '%s')" % other
            else: other = ""
            if kind is not item:
                inherited = " (from <a href=%s>%s</a>)" % (toLink(kind.itsPath), kind.itsName)
            else:
                inherited = ""
            result += "<td valign=top><a href=%s>%s</a>%s%s</td>\n" % \
             (toLink(attribute.itsPath), key, inherited, other)
            result += "<td valign=top>%s" % \
             (attribute.getAttributeValue('description', default = "&nbsp;"))
            try:
                issues = attribute.issues
                result += "<p>Issues:<ul>"
                for issue in issues:
                    result += "<li>%s\n" % issue
                result += "</ul></p>"
            except: pass
            result += "</td>\n"
            cardinality = attribute.getAttributeValue('cardinality',
             default='single')
            result += "<td valign=top>%s</td>\n" % ( cardinality )
            attrType = attribute.getAttributeValue('type', default=None)
            if attrType:
                result += "<td valign=top><a href=%s>%s</a></td>\n" % \
                 (toLink(attrType.itsPath), attrType.itsName)
            else:
                result += "<td valign=top>N/A</td>\n"
            if attribute.hasLocalAttributeValue('initialValue'):
                result += "<td valign=top>%s</td>\n" % (attribute.initialValue,)
            else:
                result += "<td valign=top>N/A</td>\n"

            # if attribute.required: result += "<td valign=top>Yes</td>\n"
            # else: result += "<td valign=top>No</td>\n"

            redirectTo = attribute.getAttributeValue('redirectTo',
             default="&nbsp;")
            result += "<td valign=top>%s</td>\n" % redirectTo

            result += "</tr>\n"
            count += 1
        result += "</table>\n"
        result += "<br />\n"

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td colspan=2><b>Attribute values for this item:</b></td>\n"
    result += "</tr>\n"
    result += "<tr class='headingsrow'>\n"
    result += "<td valign=top><b>Attribute</b></td>\n"
    result += "<td valign=top><b>Value</b></td>\n"
    result += "</tr>\n"
    count = 0

    displayedAttrs = { }
    for (name, value) in item.iterAttributeValues():
        if name is None: name = "Anonymous"
        displayedAttrs[name] = value

    keys = displayedAttrs.keys()
    keys.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
    for name in keys:
        value = displayedAttrs[name]

        if name == "attributes" or \
           name == "notFoundAttributes" or \
           name == "inheritedAttributes":
            pass

        elif name == "originalValues":
            pass

        elif isinstance(value, RefList):

            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            result += "<b>(ref coll)</b> "
            output = []
            for j in value:
                output.append("<a href=%s>%s</a>" % \
                 (toLink(j.itsPath), getattr(j, "blockName", j.getItemDisplayName())))
            result += (", ".join(output))

            result += "</td></tr>\n"
            count += 1

        elif isinstance(value, list):

            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            result += "<ul>"
            for j in value:
                try:
                    result += "<li>%s <a href=%s>%s</a><br>\n" % (j.itsName,
                     toLink(j.itsPath), j.itsPath)
                except:
                    result += "<li>%s (%s)<br>\n" % (clean(j), clean(type(j)))
            result += "</ul>"
            result += "</td></tr>\n"
            count += 1

        elif isinstance(value, dict):

            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            for key in value.keys():
                try:
                    result += "%s: %s <a href=%s>%s</a><br>" % \
                     (key, value[key].itsName, toLink( value[key].itsPath),
                      value[key].itsPath)
                except:
                    result += "%s: %s (%s)<br>" % (key, clean(value[key]),
                     clean(type(value[key])))

            result += "</td></tr>\n"
            count += 1

        elif isinstance(value, Lob):
            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            try:
                theType = TypeHandler.typeHandler(repoView,
                 value)
                typeName = theType.getImplementationType().__name__
                result += "<b>(%s)</b> " % typeName
                uStr = value.getReader().read()
                content = uStr.encode('ascii', 'replace')
                result += clean(content)

            except Exception, e:
                result += clean(str(e))
                result += "(Couldn't read Lob content)"
                raise

            result += "</td></tr>\n"
            count += 1

        elif isinstance(value, Item):
            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            result += "<b>(itemref)</b> "
            result += "<a href=%s>%s</a><br>" % (toLink(value.itsPath),
              value.getItemDisplayName())
            result += "</td></tr>\n"
            count += 1

        elif isinstance(value, URL):

            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            theType = TypeHandler.typeHandler(repoView, value)
            typeName = theType.getImplementationType().__name__
            result += "<b>(%s)</b> " % typeName
            result += ' <a href="%s">%s</a><br>' %(value, value)
            result += "</td></tr>\n"
            count += 1

        else:

            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            theType = TypeHandler.typeHandler(repoView, value)
            typeName = theType.getImplementationType().__name__
            result += "<b>(%s)</b> " % typeName
            try:
                result += "<a href=%s>%s</a><br>" % (toLink(value.itsPath),
                 value.getItemDisplayName())
            except:
                if name == "password":
                    result += "<i>(hidden)</i><br>"
                else:
                    result += "%s<br>" % (clean(value))

            result += "</td></tr>\n"
            count += 1
    result += "</table>\n"

    if isBlock:
        try:
            widget = item.widget
        except:
            pass
        else:
            result += RenderObject(repoView, widget, "%s/%s" % (item.itsPath, "widget"), "Widget")
            
    if isKind:

        # Cloud info
        result += "<br />\n"
        result += RenderClouds(repoView, item)

    if isinstance(item, ContentItem):
        result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
        result += "<tr class='toprow'>\n"
        result += "<td><b>Additional information:</b></td>\n"
        result += "</tr>\n"
        result += "<tr class='oddrow'>\n"
        result += "<td>Item version: %d<br>Is item dirty: %s<br>Shared state: %s</td>\n" % (item.getVersion(), item.isDirty(), item.sharedState)
        result += "</tr>\n"
        result += "</table>\n"

    return result

indexRE = re.compile(r"(.*)\[(\d+)\]")

def _getObjectValue(theObject, name):
    """ 
    Given an object and a name, get the value.
    If the name ends with "[\d+]", strip that off and save the index, then:
    If it's a regular attribute (not callable), get its value.
    If it's callable, call it and get the resulting value (we call twice if necessary: once with
    no parameters, once with the object as a parameter).
    Once we've got a value: if we'd gotten an index, treat the value as a list
    and return the index-th thing
    """
    index = None
    global indexRE
    m = indexRE.match(name)
    if m is not None:
        (name, index) = m.groups(1)
    attr = getattr(theObject, name, None)
    if attr is None or not callable(attr):
        return attr
    value = None
    try:
        value = attr(theObject)
    except:
        try:
            value = attr()
        except:
            pass
    if index is not None:
        value = value[int(index)]
    return value

def RenderObject(repoView, theObject, objectPath, label="Object"):
    result = "&nbsp;<br><table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td colspan=2><b>%s: %s</b></td>\n" % (clean(label), clean(theObject))
    result += "</tr>\n"
    result += "<tr class='headingsrow'>\n"
    result += "<td valign=top><b>Attribute</b></td>\n"
    result += "<td valign=top><b>Value</b></td>\n"
    result += "</tr>\n"
    count = 0
    
    displayedAttrs = { }
    for name in dir(theObject):
        if name is None:
            continue
        try:
            attr = getattr(theObject, name)
        except AttributeError:
            continue
        if callable(attr):
            if (name.endswith("Tuple") or not (name.startswith('Get') or name.startswith('Has') or name.startswith('Is'))):
                continue
            displayName = "%s()" % name
        elif name in ('__class__', '__dict__', '__doc__', '__module__', '__weakref__', 'this', 'thisown'):
            continue
        else:
            displayName = name
        value = _getObjectValue(theObject, name)
        
        displayedAttrs[displayName] = (name, value)

    keys = displayedAttrs.keys()
    keys.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
    for displayName in keys:
        (name, value) = displayedAttrs[displayName]

        result += oddEvenRow(count)
        result += "<td valign=top>"
        result += "%s" % displayName
        result += "</td><td valign=top>"
        try:
            theType = TypeHandler.typeHandler(repoView, value)
            typeName = theType.getImplementationType().__name__
            result += "<b>(%s)</b> " % typeName
        except:
            result += "<b>(%s)</b> " % value.__class__.__name__

        if isinstance(value, list):
            results = []
            for i in range(len(value)):
                v = value[i]
                if isinstance(v, object):
                    results.append("<a href=%s?mode=object>%s</a>" % (toLink("%s/%s[%d]" % (objectPath[1:], name, i)), clean(v)))
                else:
                    results.append("%s" % (clean(v)))
                    # if isinstance(v, object): # str(v).find("; proxy of C++ ") != -1:

            result += ", ".join(results) + "<br>"
        else:            
            if isinstance(value, object):
                result += "<a href=%s?mode=object>%s</a><br>" % (toLink("%s/%s" % (objectPath[1:], name)), clean(value))
            else:
                result += "%s<br>" % (clean(value))    
        result += "</td></tr>\n"
        count += 1

    result += "</table>\n"
    return result

def getItemName(item):
    try:
        name = item.getItemDisplayName()
    except:
        name = item.itsName
    if name is None:
        name = str(item.itsUUID)
    return name

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def oddEvenRow(count):
    if count % 2:
        return "<tr class='oddrow'>\n"
    else:
        return "<tr class='evenrow'>\n"

def toLink(path):
    s = "/repo/%s" % path[1:]
    return s.replace(" ", "%20")

def clean(s):
    s = str(s)
    return s.replace("<", "").replace(">","")

def indent(depth):
    result = ""
    for i in range(depth):
        result += "&nbsp;&nbsp;&nbsp;&nbsp;"
    return result

