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


import sys, string, traceback

import re
from osaf import pim, webserver, sharing
from osaf.pim.items import ContentItem
from osaf.pim.collections import ContentCollection
from repository.schema.TypeHandler import TypeHandler
from repository.item.RefCollections import RefList
from repository.item.Sets import \
    Set, MultiUnion, Union, MultiIntersection, Intersection, Difference, \
    KindSet, ExpressionFilteredSet, MethodFilteredSet

from util import inspector

import logging
logger = logging.getLogger(__name__)


class RepoResource(webserver.AuthenticatedResource):
    isLeaf = True
    def render_GET(self, request):

        cookies = request.received_cookies

        try:

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

            version = request.args.get('version', [None])[0]
            if version is not None:
                if version == "latest":
                    repoView.refresh()
                else:
                    curVer = repoView.itsVersion
                    if version == "older":
                        version = curVer - 1
                    elif version == "newer":
                        version = curVer + 1
                    else:
                        version = long(version)
                    repoView.refresh(version=version)
            version = repoView.itsVersion
            logger.info("Version: %d", version)

            request.addCookie("view", repoView.name, path="/repo")

            # deal with "dv" (show the rendered detail view) and "dvitem"
            # (show the current detail view item) modes.
            if mode is not None and mode.startswith("dv"):
                # Find the rendered detail view - we'll show it or its item.
                path = "//parcels/osaf/views/detail/DetailRootBlock"
                dvKind = repoView.findPath(path)
                renderedDVs = [ dv for dv in dvKind.iterItems(recursive=True)
                                if hasattr(dv, 'widget') ]
                if not renderedDVs:
                    # No rendered DVs? Just do a kind query to show that.
                    mode = 'kindquery'
                else:
                    currentDV = renderedDVs[0]
                    path = currentDV.itsPath
                    if mode == 'dvitem':
                        # Get the current item instead.
                        dvItem = getattr(currentDV, 'contents', None)
                        if dvItem is not None:
                            path = dvItem.itsPath
                    mode = None
                
            elif not request.postpath or not request.postpath[0]:
                path = "//"
            else:
                path = "//%s" % ("/".join(request.postpath))

            result = \
"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>Chandler : %s</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="stylesheet" href="/site.css" type="text/css" />
<script type="text/javascript" src="/jsolait/init.js"></script>
<script type="text/javascript" src="/jsolait/lib/urllib.js"></script>
<script type="text/javascript" src="/jsolait/lib/xml.js"></script>
<script type="text/javascript" src="/jsolait/lib/xmlrpc.js"></script>
<script type="text/javascript" src="/repo-editor.js"></script>
<script type="text/javascript">var repoView="%s"</script>
</head>

<body onload="onDocumentLoad()">
"""                 % (request.path, repoView.name)

            result += """
<p class="footer">Repository view: <b>%s (v%d)</b> |
<a href="?version=latest">refresh</a> |
<a href="?version=older">&lt;&lt; older</a> |
<a href="?version=newer">newer &gt;&gt;</a> |
<a href="/repo/?mode=views">switch</a> |
<a href="#" onclick="commit()">commit</a></p>
<div id="status-area">[status]</div>
""" % (repoView.name, repoView.itsVersion)

            if mode == "kindquery":
                item = repoView.findPath(path)
                result += "<div>"
                result += RenderKindQuery(repoView, item)
                result += "</div>"

            elif mode == "views":
                ensureDebugView(self.repositoryView)
                result = RenderViews(repoView)

            elif mode == "search":
                text = request.args.get('text', [None])[0]
                result += RenderSearchResults(repoView, text)

            elif mode == "blocks":
                item = repoView.findPath(path)
                path = '<a href="%s">[top]</a>' % toLink("/")
                i = 2
                for part in item.itsPath[1:-1]:
                    path += ' &gt; <a href="%s">%s</a>' % (toLink(item.itsPath[:i]), part)
                    i += 1

                name = item.itsName
                if name is None:
                    name = unicode(item.itsUUID)
                result += '<div class="path">%s &gt; <span class="itemname"><a href="%s">%s</a></span> | <a href="%s">Render attributes</a></div>' % (path, toLink(item.itsPath), name, toLink(item.itsPath))

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
                    result = result.encode('utf-8', 'replace')
                    return result

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
                        return result.encode('utf-8', 'replace')
                result += "<div>"
                result += RenderObject(repoView, theValue, path)
                result += "</div>"

            elif mode == "inheritance":
                result += RenderInheritance(repoView)

            elif path != "//":
                logger.info("path: [%s]", path)
                splitPath = path.split("/")
                logger.info("path: [%s] %s", path, splitPath)
                if splitPath[2] == 'uuid':
                    uuid = splitPath[3]
                    logger.info("uuid: [%s]", uuid)
                    item = repoView.findUUID(uuid)
                else:
                    item = repoView.findPath(path)

                if item is None:
                    result += "<h3>Item not found</h3>"
                    result = result.encode('utf-8', 'replace')
                    return result

                if mode == "history":
                    result += "<div>"
                    result += RenderHistory(repoView, item)
                    result += "</div>"
                else:
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

        except Exception, e: 
            result = "<html>Caught a %s exception: %s<br> %s</html>" % (type(e), e, "<br>".join(traceback.format_tb(sys.exc_traceback)))

        return result.encode('utf-8', 'replace')


def RenderSearchForm(repoView):
    result = """
<table width="100%" border="0" cellpadding="4" cellspacing="0" class="search-form">
<tr class="toprow">
<td><b>PyLucene Search:</b></td>
</tr>
<tr class="oddrow">
<td>
    <div class="tree">
    <form method="get" action="/repo"><input type="text" name="text" size="40"><input type="hidden" name="mode" value="search"></form>
</div>
</td></tr></table>
"""

    return result

def RenderSearchResults(repoView, text):
    result = u""
    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>PyLucene Search Results for <i>%s</i> :</b></td>\n" % text
    result += "</tr>\n"
    count = 0
    for (item, attribute) in repoView.searchItems(text):
        result += oddEvenRow(count)
        result += '<td><a href="%s">%s</a></td>' % (toLink(item.itsPath), getItemName(item))
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
        result += '<a href="%s">//%s</a> &nbsp;  ' % (toLink(child.itsPath), child.itsName)
    result += "</div>"
    result += "</td></tr></table>\n"
    return result


def ensureDebugView(repoView):
    for view in repoView.views:
        if view.name == "debug":
            return
    repoView.repository.createView("debug")

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
    result = u""
    kinds = []
    for item in repoView.findPath("//Schema/Core/Kind").iterItems():
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
        result += '<td><a href="%s">%s</a></td>' % (toLink(item.itsPath), getItemName(item))
        result += "<td>"
        klass = None
        if hasattr(item, 'classes'):
            klass = item.classes['python']
            result += clean(unicode(klass))
        result += "</td>"
        result += "<td>"
        if klass is not None:
            if hasattr(klass, 'getKind'):
                checkKind = klass.getKind(repoView)
                result += unicode(checkKind.itsPath)
                if checkKind is item:
                    result += " (ok)"
                else:
                    result += " <b>(MISMATCH)</b>"
        result += "</td>"
        result += "<td>"
        if klass is not None:
            for superclass in klass.__bases__:
                result += clean(superclass) + ", "
        result += "</td>"

        result += "<td>"
        for superKind in item.superKinds:
            result += getItemName(superKind) + ", "
        result += "</td>"
        result += "</tr>"
        count += 1
    result += "</table>\n"

    return result

def RenderKinds(repoView):
    result = ""
    items = {}
    tree = {}
    for item in repoView.findPath("//Schema/Core/Kind").iterItems():
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
    keys.sort(key=string.lower)
    output = []
    for key in keys:
        if key == "":
            continue
        if node[key].has_key(""):
            item = node[key][""]
            output.append('<a href="%s">%s</a>' % (toLink(item.itsPath), 
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
            result += "<li>"
            result += "<b>%s</b>" % key
            result += _RenderNode(repoView, node[key], depth+1)
            result += "</ul>"

    return result


def _getAllClouds(kind):
    """ A generator which returns every cloud for a given kind.  """

    clouds = getattr(kind, 'clouds', None)
    if clouds:
        for cloud in clouds:
            yield (cloud, cloud.kind.clouds.getAlias(cloud))

    superKinds = getattr(kind, 'superKinds', None)
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
    for cloud in repoView.findPath("//Schema/Core/Cloud").iterItems():
        clouds[cloud.itsPath] = cloud
    keys = clouds.keys()
    keys.sort()
    for key in keys:
        cloud = clouds[key]
        result += "<p>"
        result += 'Cloud <a href="%s">%s</a> for kind <a href="%s">%s</a>' % \
         (toLink(cloud.itsPath), cloud.itsPath, toLink(cloud.kind.itsPath), 
         cloud.kind.itsName)
        alias = cloud.kind.clouds.getAlias(cloud)
        if alias:
            result += " (alias '%s')" % alias
        result += "<br>"
        for endpoint in cloud.endpoints:
            result += '&nbsp;&nbsp;&nbsp;Endpoint <a href="%s">%s</a>:' % (toLink(endpoint.itsPath), endpoint.itsName)
            result += " attribute '"
            result += (".".join(endpoint.attribute))
            result += "', "
            alias = cloud.endpoints.getAlias(endpoint)
            if alias:
                result += " (alias '%s')" % alias
            result += " policy '%s'" % endpoint.includePolicy
            if endpoint.includePolicy == "byCloud":
                if getattr(endpoint, 'cloud', None) is not None:
                    result += ' --&gt; <a href="%s">%s</a>' % (toLink(endpoint.cloud.itsPath), endpoint.cloud.itsName)
                elif getattr(endpoint, 'cloudAlias', None) is not None:
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
                if getattr(endpoint, 'cloud', None) is not None:
                    result += " --&gt; <a href=%s>%s</a>" % (toLink(endpoint.cloud.itsPath), endpoint.cloud.itsName)
                elif getattr(endpoint, 'cloudAlias', None) is not None:
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

    result = u""

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
        items = []
        for i in item.iterItems(recursive=True):
            items.append(i)
        items.sort(key=lambda x: getItemName(x).lower())
        for i in items:
            output.append("<a href=%s>'%s'</a>  (%s) %s %s" % \
                          (toLink(i.itsPath), getItemName(i),
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

    if block.childBlocks.refCount(False) == 0:
        hasChildren = False
    else:
        hasChildren = True

    result = ""
    if hasChildren:
        result += "<table class=block width=100%%>"
    else:
        result += "<table class=childlessblock width=100%%>"
    result += "<tr class=block><td class=block valign=top><a href=%s?mode=blocks>%s</a><a href=%s>%s</a></td></tr>" % (
        toLink(block.itsPath), name, toLink(block.itsPath), block.isShown and ' +' or ' -')

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
        result += '<tr class="block">'

    for child in block.childBlocks:
        childRender = RenderBlock(repoView, child)
        if mode == 'horizontal':
            result += '<td class="block" valign="top" >%s</td>' % childRender
        else:
            result += '<tr class="block"><td class="block" width="100%%">%s</td></tr>' % childRender

    if mode == 'horizontal':
        result += "</tr>"

    result += "</table>"
    return result


class ValueRenderer(object):
    """
    At the moment, this is just a class-level container for rendering methods,
    where each method just returns a string
    """
    def __init__(self, item):
        self.item = item


    def Render(self, name):
        value = getattr(self.item, name)
        return self.RenderValue(value, name)
        
    def RenderValue(self, value, name=''):
        # we're guaranteed that we'll fall all the way back to Render_object
        if hasattr(value, '__class__'):
            for cls in value.__class__.__mro__:
                renderMethod = getattr(self, 'Render_' + cls.__name__, None)
                if renderMethod is not None:
                    return renderMethod(name, value)
            
    def __str__(self):
        return self.renderMethod()

    def Render_RefList(self, name, value):
        itemString = "<b>(ref collection)</b>"
        if value:
            itemString += "\n<ul>"
            output = []
            for j in value:
                alias = value.getAlias(j)
                if alias:
                    alias = "(alias = '%s')" % alias
                else:
                    alias = ""
                output.append('<li><span class="editable">%s</span> <a href=%s>%s</a> %s</li>' % \
                 ( getattr(j, "blockName", getItemName(j)), toLink(j.itsPath), j.itsPath, alias))
            itemString += ("".join(output))    
            itemString += "</ul>"
        else:
            itemString = "<i>(empty)</i>"

        return itemString

    def Render_list(self, name, value):
        itemString = "<ul>"
        for j in value:
            try:
                itemString += ('<li><span class="editable">%s</span> <a href="%s">%s</a></li>\n' %
                               (j.itsName, toLink(j.itsPath), j.itsPath))
            except:
                itemString += "<li>%s (%s)</li>\n" % (clean(j), clean(type(j)))
        else:
            itemString = "<i>(empty)</i>"
        return itemString

    def Render_dict(self, name, value):
        if value:
            itemString = ""
            for key, entryValue in value.iteritems():
                try:
                    itemString += (
                        '<span class="editable">%s</span>: %s '
                        '<a href=%s>%s</a><br>' % 
                        (key, entryValue.itsName,
                         toLink(entryValue.itsPath),
                         entryValue.itsPath))
                except:
                    try:
                        itemString += ("%s: %s (%s)<br>" %
                                       (key, clean(entryValue),
                                        clean(type(entryValue))))
                    except:
                        itemString += "%s: <i>(Can't display)</i> (%s)<br>" % \
                            (key, clean(type(entryValue)))
        else:
            itemString = "<i>(empty)</i>"
                    
        return itemString

    Render_RefDict = Render_dict

    def Render_Lob(self, name, value):
        itemString = ""
        mimeType = value.mimetype
        if mimeType.startswith("image/"):
            itemString += "<img src=/lobs/%s/%s><br>" % (self.item.itsUUID, name)
            itemString += "(%s)<br>" % mimeType
        else:
            try:
                theType = TypeHandler.typeHandler(self.item.itsView,
                                                  value)
                typeName = theType.getImplementationType().__name__
                itemString += "<b>(%s)</b> " % typeName
                content = value.getReader().read()
                itemString += '<span class="editable">%s</span>' % clean(content)

            except Exception, e:
                itemString += clean(e)
                itemString += "(Couldn't read Lob content)"
                
        return itemString

    def Render_Item(self, name, value):
        return '%s <a href="%s">%s</a><br>' % (getItemName(value),
                                               toLink(value.itsPath),
                                               value.itsPath)
    def Render_URL(self, name, value):
        theType = TypeHandler.typeHandler(self.item.itsView, value)
        typeName = theType.getImplementationType().__name__
        itemString = '<b>(%s)</b> ' % typeName
        itemString += ' <a href="%s">%s</a><br>' %(value, value)

        return itemString

    def Render_AbstractSet(self, name, value):
        theType = TypeHandler.typeHandler(self.item.itsView, value)
        typeName = theType.getImplementationType().__name__

        itemString = "<b>(%s)</b> " % typeName

        if value:
            itemString += "<ul>"
            for j in value:
                itemString += ('<li>%s</li>\n' % self.RenderValue(j))
                #itemString += ('<li>%s <a href="%s">%s</a><br>\n' %
                               #(getItemName(j),
                                #toLink(j.itsPath), j.itsPath))
            itemString += "</ul>"
        else:
            itemString += "<i>(empty)</i>"

        if getattr(value,'_indexes', None):
            itemString += "<br>Indexes in %s:<ul>\n" % name
            if value._indexes:
                for indexName in value._indexes:
                    itemString += "<li>" + indexName
                    if value.getRanges(indexName):
                        itemString += ", ranges: %s" % (value.getRanges(indexName),)
                    itemString += "</li>\n"
                itemString += "</ul>\n"
            else:
                itemString += "<i>(none)</i>"

        return itemString

    Render_PersistentSet = Render_AbstractSet

    def Render_object(self, name, value):
        """ Default renderer """
        theType = TypeHandler.typeHandler(self.item.itsView, value)
        typeName = theType.getImplementationType().__name__
        itemString = "<b>(%s)</b> " % typeName
        try:
            itemString += "<a href=%s>%s</a><br>" % (
                toLink(value.itsPath),
                getItemName(value))
        except:
            if name == "password":
                itemString += "<i>(hidden)</i><br>"
            else:
                itemString += '<span class="editable">%s</span><br>' % \
                              clean(value)
                
        return itemString
        

def RenderItem(repoView, item):

    result = u""

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
        name = '{%s}' % item.itsUUID.str64()
    result += '<div class="path">%s &gt; <span class="itemname">%s</span>\n' % (path, name)

    result += '<script>var itemPath = "%s";</script>\n' % item.itsPath
    try: result += ' (<a href="%s">%s</a>)' % (toLink(item.itsKind.itsPath), item.itsKind.itsName)
    except: pass

    if isKind:
        result += ' | Run a <a href="%s?mode=kindquery">Kind Query</a>' % toLink(item.itsPath)
    else:
        result += ' | <a href="%s?mode=history">Show history</a>' % toLink(item.itsPath)

    if isBlock:
        result += ' | <a href="%s?mode=blocks">Render block tree</a>' % toLink(item.itsPath)

    result += "</div>\n"

    try:
        displayName = item.displayName
        #This will upcast the string to unicode since displayName is unicode
        result += "<div class='subheader'><b>Display Name:</b> %s</div>\n" % displayName
    except:
        pass

    result += "<div class='subheader'><b>itsUUID:</b> %s<br> " % item.itsUUID
    result += "<div class='children'><b>Child items:</b><br> "
    children = {}
    for child in item.iterChildren():
        name = child.itsName
        if name is None:
            name = unicode(child.itsUUID)
        children[name] = child
    keys = children.keys()
    keys.sort(key=string.lower)
    output = []
    for key in keys:
        child = children[key]
        name = child.itsName
        displayName = ""
        if name is None:
            name = unicode(child.itsUUID)
            displayName = getItemName(child)
        children[name] = child
        output.append(" &nbsp; <a href=%s>%s </a> %s" % (toLink(child.itsPath), key, displayName))
    if not output:
        result += " &nbsp; None"
    else:
        result += ("<br>".join(output))
    result += "</div>\n"


    if isKind:
        result += """
<table width=100% border=0 cellpadding=4 cellspacing=0>\n
  <tr class="toprow">
    <td colspan="7"><b>Attributes defined for this kind:</b></td>
  </tr>
  <tr class="headingsrow">
    <td valign="top"><b>Attribute</b> (inherited from)</td>
    <td valign="top"><b>Description / Issues</b></td>
    <td valign="top"><b>Cardinality</b></td>
    <td valign="top"><b>Type</b></td>
    <td valign="top"><b>Initial&nbsp;Value</b></td>
    <!-- <td valign="top"><b>Required?</b></td> -->
  </tr>"""
        count = 0
        displayedAttrs = { }
        for name, attr, kind in item.iterAttributes():
            if name is None: name = "Anonymous"
            displayedAttrs[name] = (attr, kind)
        keys = displayedAttrs.keys()
        keys.sort(key=string.lower)
        for key in keys:
            attribute, kind = displayedAttrs[key]
            result += oddEvenRow(count)
            other = getattr(attribute, 'otherName', "")
            if other: other = " (inverse: '%s')" % other
            else: other = ""
            if kind is not item:
                inherited = " (from <a href=%s>%s</a>)" % (toLink(kind.itsPath), kind.itsName)
            else:
                inherited = ""
            result += "<td valign=top><a href=%s>%s</a>%s%s</td>\n" % \
             (toLink(attribute.itsPath), key, inherited, other)
            result += "<td valign=top>%s" % \
             (getattr(attribute, 'description', "&nbsp;"))
            result += "</td>\n"
            cardinality = getattr(attribute, 'cardinality', 'single')
            result += "<td valign=top>%s</td>\n" % ( cardinality )
            attrType = getattr(attribute, 'type', None)
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

            result += "</tr>\n"
            count += 1
        result += "</table>\n"
        result += "<br />\n"

    result += """
<table width="100%" border="0" cellpadding="4" cellspacing="0" onclick="onValueTableClick(event)">
  <tr class="toprow">
    <td colspan="2"><b>Attribute values for this item:</b></td>
  </tr>
  <tr class="headingsrow">
    <td valign="top"><b>Attribute</b></td>
    <td valign="top"><b>Value</b></td>
  </tr>
"""
    count = 0

    displayedAttrs = { }
    for (name, value) in item.iterAttributeValues():
        if name is None: name = "Anonymous"
        displayedAttrs[name] = value

    keys = displayedAttrs.keys()
    keys.sort(key=string.lower)

    def MakeValueRow(attributeName, attributeValue, attributeType):
        result = oddEvenRow(count)
        result += '<td valign="top">%s</td><td valign="top"><div class="type-%s attr-%s">%s</div></td></tr>\n' % (attributeName, attributeType, attributeName, attributeValue)
        return result

    vr = ValueRenderer(item)
    
    for name in keys:
        value = displayedAttrs[name]
        valueType = type(value).__name__

        if name in ("attributes",
                    "notFoundAttributes",
                    "inheritedAttributes",
                    "originalValues"):
            continue



        try:
            itemString = vr.Render(name)
        except Exception, e:
            itemString = "Couldn't render %s: <br/><pre>%s</pre>" % (name, traceback.format_exc())

        result += MakeValueRow(name, itemString, valueType)
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

    if isinstance(item, ContentCollection):
        result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
        result += "<tr class='toprow'>\n"
        result += "<td><b>Collection Sources:</b></td>\n"
        result += "</tr>\n"
        result += "<tr class='oddrow'>\n"
        result += "<td>%s</td>\n" % _getSourceTree(item)
        result += "</tr>\n"
        result += "</table>\n"

    if isinstance(item, ContentItem):
        result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
        result += "<tr class='toprow'>\n"
        result += "<td><b>Additional information:</b></td>\n"
        result += "</tr>\n"
        result += "<tr class='oddrow'>\n"
        result += "<td>Item version: %d<br>Is item dirty: %s</td>\n" % (item.getVersion(), item.isDirty())
        result += "</tr>\n"
        result += "</table>\n"

    if isinstance(item, pim.Note):
        if pim.has_stamp(item, sharing.SharedItem):
            si = sharing.SharedItem(item)
            for share in si.sharedIn:
                conduit = share.conduit
                if isinstance(conduit, sharing.RecordSetConduit):
                    trans = conduit.translator(repoView)
                    filter = conduit.getFilter()
                    if filter is None:
                        filter = lambda rs: rs
                    else:
                        filter = filter.sync_filter
                    alias = trans.getAliasForItem(item)
                    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
                    result += "<tr class='toprow'>\n"
                    result += "<td><b>Shared in collection: %s</b></td>\n" % \
                        getattr(share.contents, 'displayName', 'untitled')
                    result += "</tr>\n"
                    result += "<tr class='oddrow'>\n"
                    result += "<td>Alias: %s</td>\n" % alias
                    result += "</tr>\n"

                    result += "<tr class='headingsrow'><td><b>Current Values:</b></td></tr>\n"
                    local = sharing.RecordSet(trans.exportItem(item))
                    count = 0
                    for record in sharing.sort_records(local.inclusions):
                        result += oddEvenRow(count)
                        result += "<td>%s</td>\n" % str(record)
                        result += "</tr>\n"
                        count += 1

                    if conduit.hasState(alias):
                        state = conduit.getState(alias)
                    else:
                        state = None
                    if state is not None:
                        agreed = state.agreed
                        result += "<tr class='headingsrow'><td><b>Agreed State:</b></td></tr>\n"
                        count = 0
                        for record in sharing.sort_records(agreed.inclusions):
                            result += oddEvenRow(count)
                            result += "<td>%s</td>\n" % str(record)
                            result += "</tr>\n"
                            count += 1
                        result += "<tr class='headingsrow'><td><b>Pending Changes:</b></td></tr>\n"
                        count = 0
                        for record in sharing.sort_records(state.pending.inclusions):
                            result += oddEvenRow(count)
                            result += "<td>++ %s</td>\n" % str(record)
                            result += "</tr>\n"
                            count += 1
                        for record in sharing.sort_records(state.pending.exclusions):
                            result += oddEvenRow(count)
                            result += "<td>-- %s</td>\n" % str(record)
                            result += "</tr>\n"
                            count += 1
                        result += "<tr class='headingsrow'><td><b>Pending Removal: %s</b></td></tr>\n" % ("Yes" if state.pendingRemoval else "No")

                        diff = filter(local - agreed)

                        result += "<tr class='headingsrow'><td><b>Local Changes:</b></td></tr>\n"
                        count = 0
                        for record in sharing.sort_records(diff.inclusions):
                            result += oddEvenRow(count)
                            result += "<td>++ %s</td>\n" % str(record)
                            result += "</tr>\n"
                            count += 1
                        for record in sharing.sort_records(diff.exclusions):
                            result += oddEvenRow(count)
                            result += "<td>-- %s</td>\n" % str(record)
                            result += "</tr>\n"
                            count += 1

                result += "</table>\n"

        if pim.has_stamp(item, pim.EventStamp) and item.hasLocalAttributeValue('inheritTo'):
            result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
            result += "<tr class='toprow'>\n"
            result += "<td colspan=5><b>Recurrence information: </b></td>\n"
            result += "</tr>\n"
            occurrences = sorted(list(item.inheritTo),
                key = lambda x: pim.EventStamp(x).startTime)
            count = 0
            result += "<tr class='headingsrow'><td>Start time</td><td>isGenerated</td><td>TriageOnly<td>Triage Status</td><td>DisplayName</td></tr>\n"
            for occurrence in occurrences:
                ocEvent = pim.EventStamp(occurrence)
                result += oddEvenRow(count)
                result += "<td><a href='%s'>%s</a></td>" % (toLink(occurrence.itsPath), ocEvent.startTime)
                result += "<td>%s</td>" % ocEvent.isGenerated
                result += "<td>%s</td>" % (ocEvent.isTriageOnlyModification()
                    if not ocEvent.isGenerated else "n/a")
                result += "<td>%s</td>" % occurrence._triageStatus
                result += "<td>%s</td>" % occurrence.displayName
                result += "</tr>\n"
                count += 1
            result += "</table>\n"


    return result

def RenderHistory(repoView, item):

    result = """
<table width="100%" border="0" cellpadding="4" cellspacing="0" onclick="onValueTableClick(event)">
  <tr class="toprow">
    <td colspan="2"><b>Item history</b></td>
  </tr>
  """

    count = 0


    for version, values in inspector.iterItemHistory(repoView, item.itsUUID):
        result += "<tr class='headingsrow'><td valign='top'><b>Version %d</b></td><td valign='top'></td></tr>\n" % version

        for name, value in values:
            result += oddEvenRow(count)
            result += '<td valign="top">%s</td><td valign="top">%s</td></tr>\n' % (name, clean(value))

            count += 1

    result += "</table>\n"

    return result

class HTMLCollectionRenderer(object):
    joinSymbols = { "Union" : "&cup;",
                    "Intersection" : "&cap;",
                    "Difference" : "-",
                    "Set": "[S]"}

    def __init__(self, view):
        self.view = view

    def formatCollection(self, collection, childstring, attrName = None):
        linkText = getItemName(collection)
        if attrName is not None:
            linkText = linkText + "." + attrName
        result = ('<div class="set-item">\n'
                  '  <div class="set-title">' +
                  '  <a href="%s" title="%s">%s</a>' % (
            toLink(collection.itsPath),
            collection.__class__.__name__,
            linkText) +
                  '  </div>\n' +
                  '  <div class="set-box">' +
                  childstring + '</div>\n'
                  '</div>\n')
        
        return result
    
    def formatMultiSource(self, type, hasItem, childstrings):
        if len(childstrings) == 0:
            return "empty %s" % self.joinSymbols[type]
        else:
            # wrap each item with set-box
            symbol = '</div><div class="operator">%s</div><div class="set-box">\n' % self.joinSymbols[type]
            result = '<div class="set-box">%s</div>\n' % symbol.join(childstrings)
            # if we're not inside an item, we'll need our own item...
            if not hasItem:
                result = '<div class="set-item">%s</div>\n' % result
            return result

    def formatRefList(self, refList):
        return "[%s]" % refList.__class__.__name__

    def formatExpressionFilteredSet(self, filteredSet, childstring):
        return ('<div class="operator"><abbr title="%s">filter</title></div>\n%s' % (filteredSet.filterExpression, childstring))

    def formatMethodFilteredSet(self, filteredSet, childstring):
        return ('<div class="operator"><abbr title="%s">filter</title></div>\n%s' % (filteredSet.filterMethod, childstring))

    def formatKindSet(self, cls):
        return "[all <em>%s</em>s]" % cls.__name__

    def formatUnknown(self, s):
        return "[Unknown: %s]" % (s,)

def _getSourceTree(coll, depth=0):
    result = ""

    view = coll.itsView
    formatter = HTMLCollectionRenderer(view)

    joinTypes = { Difference: 'Difference',
                  Union: 'Union',
                  Intersection: 'Intersection',
                  MultiUnion: 'Union',
                  MultiIntersection: 'Intersection',
                  Set: 'Set' }

    def getstring(s, hasItem=False):

        if isinstance(s, pim.ContentCollection):
            set = getattr(s, s.__collection__)
            result = formatter.formatCollection(s, getstring(set, True))
        
        elif isinstance(s, tuple):
            item = view.find(s[0], False)
            if item is None:
                result = '<em>deleted:</em>(%s, %s)' % (s[0], s[1])
            else:
                attribute = s[1]
                set = getattr(item, attribute)
                if attribute != getattr(item, '__collection__', None):
                    result = formatter.formatCollection(item, getstring(set, True),
                                                        attribute)
                else:
                    result = formatter.formatCollection(item, getstring(set, True))
            
        elif s.__class__ in joinTypes:
            if hasattr(s, '_sources'):
                result = formatter.formatMultiSource(joinTypes[s.__class__],
                                                     hasItem,
                                                   map(getstring, s._sources))
            elif hasattr(s, '_left'):
                result = formatter.formatMultiSource(joinTypes[s.__class__],
                                                     hasItem,
                                                   (getstring(s._left),
                                                    getstring(s._right)))
            elif hasattr(s, '_source'):
                result = formatter.formatMultiSource(joinTypes[s.__class__],
                                                     hasItem,
                                                     (getstring(s._source),))
            else:
                result = "???"
        
        elif isinstance(s, RefList):
            result = formatter.formatRefList(s)
        
        elif isinstance(s, ExpressionFilteredSet):
            result = formatter.formatExpressionFilteredSet(s, getstring(s._source))
        
        elif isinstance(s, MethodFilteredSet):
            result = formatter.formatMethodFilteredSet(s, getstring(s._source))
        
        elif isinstance(s, KindSet):
            cls = view[s._extent].kind.classes['python']
            result = formatter.formatKindSet(cls)
        
        else:
            result = formatter.formatUnknown(s)

        return result

    # now look at the actual set structure
    return getstring(coll)

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
        except (AttributeError, TypeError):
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
            try:
                result += "<b>(%s)</b> " % value.__class__.__name__
            except Exception, e:
                result += "<b>(%s)</b> " % e

        if isinstance(value, list) or value.__class__.__name__ == "WindowList":
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
    return clean(getattr(item, 'displayName', None) or item._repr_())
    name = getattr(item, 'displayName', None)
    if not name:
        reprMethod = getattr(item, '_repr_', None)
        if reprMethod:
            name = reprMethod()
        else:
            name = "%s" % item
    return clean(name)

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
    s = unicode(s)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

