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


import os, sys, re, string, errno, shutil, time
import repository

from application import Globals, Utility, schema
from repository.item.RefCollections import RefList
from chandlerdb.item.c import isitemref


def generateModelDocs(options, outputDir=None):
    urlRoot       = '/docs/current/model'
    chandlerDir   = Utility.locateChandlerDirectory()
    repositoryDir = Utility.locateRepositoryDirectory(chandlerDir, options)

    if not outputDir:
        modelDir = os.path.join(chandlerDir, 'docs', 'model')
    else:
        modelDir = os.path.join(outputDir, 'model')

    options.ramdb  = True # force ramdb
    options.create = True # force a repository wipe

    parcelPath, plugins = Utility.initParcelEnv(options, chandlerDir)
    view = Utility.initRepository(repositoryDir, options)

    Utility.initParcels(options, view, parcelPath, plugins=plugins)

    if not os.path.isdir(modelDir):
        _mkdirs(modelDir)

    conf = { 'directory': modelDir,
             'urlRoot':   urlRoot,
             'css':       '%s/schema.css' % urlRoot,
           }

    for root in view.iterRoots(): 
        processItem(root, generateSchemaDocument, conf)

    generateIndex(view, conf)
 
    shutil.copy(os.path.join(chandlerDir, 'tools', 'schema.css'),
                os.path.join(modelDir, 'schema.css'))

    Utility.stopRepository(view)


def processItem(item, handler, conf):
    if item.itsName is None:
        # Skip all the unnamed items, otherwise they'll flood your disk over
        # time unless you completely blow away the doc tree before each publish
        return

    handler(item, conf)

    for child in item.iterChildren():
        processItem(child, handler, conf)


def generateSchemaDocument(item, conf):
    try: label = item.itsKind.itsName
    except: label = ""

    path = str(item.itsPath[1:])
    dir = os.path.join(conf['directory'], path)
    _mkdirs(dir)
    index = os.path.join(dir, 'index.html')
    print index
    header =  "<html><head>\n"
    header += "<title>%s %s - Chandler Schema Documentation</title>\n" % (item.itsName, label)
    header += "<link rel='stylesheet' href='%s' type='text/css' />\n" % conf['css']
    header += "</head><body>\n"
    body = RenderItem(item, conf['urlRoot'])
    footer = "</body></html>"
    out = file(index, 'w')
    out.write(header)
    out.write(body)
    out.write(generateTimestamp())
    out.write(footer)
    out.close()


def generateIndex(view, conf):
    index = os.path.join(conf['directory'], 'index.html')
    print index
    header =  "<html><head>\n"
    header += "<title>Chandler Schema Documentation</title>\n"
    header += "<link rel='stylesheet' href='%s' type='text/css' />\n" % conf['css']
    header += "</head><body>\n"
    body = "<div class='header'>Chandler Schema Documentation</div>"
    body += RenderKinds(view, conf['urlRoot'])
    footer = "</body></html>"
    out = file(index, 'w')
    out.write(header)
    out.write(body)
    out.write(generateTimestamp())
    out.write(footer)
    out.close()


def generateTimestamp():
    result = "<div class='footer'>Generated on %s</div>" % \
     time.strftime("%B %d, %Y at %I:%M:%S %p %Z")
    return result


def RenderKinds(view, urlRoot):
    result = ""
    items  = {}
    tree   = {}

    for item in view.findPath("//Schema/Core/Kind").iterItems():
        items[item.itsPath] = item
        _insertItem(tree, item.itsPath[1:], item)

    result += "<table width=100% border=0 cellpadding=4 cellspacing=0>\n"
    result += "<tr class='toprow'>\n"
    result += "<td><b>All kinds defined in the data model and domain model:</b></td>\n"
    result += "</tr>\n"

    result += "<tr class='oddrow'>\n"
    result += "<td>"
    result += "<div class='tree'>"
    result += _RenderNode(tree, urlRoot)
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


def _RenderNode(node, urlRoot, depth=1):
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
            output.append("<a href=%s>%s</a>" % (toLink(urlRoot, item.itsPath), 
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
            result += _RenderNode(node[key], urlRoot, depth+1)
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


def RenderClouds(kind, urlRoot):
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
            result += "<a href=%s>%s</a> in cloud %s: " % (toLink(urlRoot, endpoint.itsPath), endpoint.itsName, foundInCloud.itsPath)
            if alias:
                result += " (alias '%s')" % alias
            result += " policy '%s'" % endpoint.includePolicy
            if endpoint.includePolicy == "byCloud":
                if endpoint.getAttributeValue('cloud', default=None) is not \
                 None:
                    result += " --&gt; <a href=%s>%s</a>" % (toLink(urlRoot, endpoint.cloud.itsPath), endpoint.cloud.itsName)
                elif endpoint.getAttributeValue('cloudAlias', default=None) \
                 is not None:
                    result += " to cloud alias '%s'" % endpoint.cloudAlias
            result += "<br>\n"
        result += "</td></tr>\n"
        count += 1
    result += "</table>\n"
    return result


def RenderCloudItems(rootItem, urlRoot):
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
            (toLink(urlRoot, item.itsPath), item.itsName))
        result += (", ".join(output))
        result += " (References included: "
        output = []
        for ref in references.itervalues():
            output.append("<a href=%s>%s</a>" % \
             (toLink(urlRoot, ref.itsPath), ref.itsName))
        result += (", ".join(output))
        result += ")"
        result += "<br>"

    return result

def RenderItem(item, urlRoot):

    result = ""
    # For Kinds, display their attributes (except for the internal ones
    # like notFoundAttributes):
    isKind = \
     (item.itsKind and "//Schema/Core/Kind" == str(item.itsKind.itsPath))

    path = "<a href=%s>[top]</a>" % toLink(urlRoot, "/")
    i = 2
    for part in item.itsPath[1:-1]:
        path += " &gt; <a href=%s>%s</a>" % (toLink(urlRoot, item.itsPath[:i]), part)
        i += 1

    result += "<div class='path'>%s &gt; <span class='itemname'>%s</span>" % (path, item.itsName)

    try: result += " (<a href=%s>%s</a>)" % (toLink(urlRoot, item.itsKind.itsPath), item.itsKind.itsName)
    except: pass
    result += "</div>\n"

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

    result += "<div class='children'><b>Child items:</b> "
    children = {}

    for child in item.iterChildren():
        # if isinstance(child, Kind) or isinstance(child, Attribute) or isinstance(child, Type) or isinstance(child, Cloud) or isinstance(child, Endpoint) or isinstance(child, Parcel):
        name = child.itsName
        if name is None: name = str(child.itsUUID)
        children[name] = child
    keys = children.keys()

    keys.sort(lambda x, y: cmp(string.lower(x), string.lower(y)))
    output = []
    for key in keys:
        child = children[key]
        output.append("<a href=%s>%s</a>" % (toLink(urlRoot, child.itsPath), key))
    if not output:
        result += " None"
    else:
        result += (", ".join(output))
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
        result += "<td valign=top><b>Required?</b></td>\n"
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
                inherited = " (from <a href=%s>%s</a>)" % (toLink(urlRoot, kind.itsPath), kind.itsName)
            else:
                inherited = ""
            result += "<td valign=top><a href=%s>%s</a>%s%s</td>\n" % \
             (toLink(urlRoot, attribute.itsPath), key, inherited, other)
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
                 (toLink(urlRoot, attrType.itsPath), attrType.itsName)
            else:
                result += "<td valign=top>N/A</td>\n"
            if attribute.hasLocalAttributeValue('initialValue'):
                result += "<td valign=top>%s</td>\n" % (attribute.initialValue,)
            else:
                result += "<td valign=top>N/A</td>\n"
            if attribute.required: result += "<td valign=top>Yes</td>\n"
            else: result += "<td valign=top>No</td>\n"

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
            output = []
            for j in value:
                output.append("<a href=%s>%s</a>" % \
                 (toLink(urlRoot, j.itsPath), j.itsName))
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
                     toLink(urlRoot, j.itsPath), j.itsPath)
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
                     (key, value[key].itsName, toLink(urlRoot,
                     value[key].itsPath), value[key].itsPath)
                except:
                    result += "%s: %s (%s)<br>" % (key, clean(value[key]),
                     clean(type(value[key])))

            result += "</td></tr>\n"
            count += 1

        elif isitemref(value):
            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            target = item.getAttributeValue(name, default=None)
            if target is not None:
                result += "<a href=%s>%s</a><br>" % (toLink(urlRoot,
                 target.itsPath), target.itsName)
            else:
                result += " None"
            result += "</td></tr>\n"
            count += 1

        else:

            result += oddEvenRow(count)
            result += "<td valign=top>"
            result += "%s" % name
            result += "</td><td valign=top>"
            try:
                result += "<a href=%s>%s</a><br>" % (toLink(urlRoot,
                 value.itsPath), value.itsName)
            except:
                result += "%s (%s)<br>" % (clean(value), clean(type(value)))

            result += "</td></tr>\n"
            count += 1
    result += "</table>\n"

    if isKind:

        # Cloud info
        result += "<br />\n"
        result += RenderClouds(item, urlRoot)

    return result


def oddEvenRow(count):
    if count % 2:
        return "<tr class='oddrow'>\n"
    else:
        return "<tr class='evenrow'>\n"


def toLink(urlRoot, path):
    if urlRoot == "":
        s = "%s" % path[1:]
    else:
        s = "%s/%s" % (urlRoot, path[1:])
    #print "creating link [%s|%s] [%s]" % (urlRoot, path[1:], s)
    return s.replace(" ", "%20")


def clean(s):
    s = str(s)
    return s.replace("<", "").replace(">","")


def indent(depth):
    result = ""
    for i in range(depth):
        result += "&nbsp;&nbsp;&nbsp;&nbsp;"
    return result


def _mkdirs(newdir, mode=0777):
    try:
        os.makedirs(newdir, mode)
    except OSError, err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(newdir):
            raise


  # "borrowed" verbatim from the python setuptools sandbox
  # http://cvs.sourceforge.net/viewcvs.py/python/python/nondist/sandbox/setuptools/setuptools/__init__.py?view=markup

def find_packages(where='.', exclude=()):
    """
    Return a list all Python packages found within directory 'where'

    'where' should be supplied as a "cross-platform" (i.e. URL-style) path; it
    will be converted to the appropriate local path syntax.  'exclude' is a
    sequence of package names to exclude; '*' can be used as a wildcard in the
    names, such that 'foo.*' will exclude all subpackages of 'foo' (but not
    'foo' itself).
    """
    from distutils.util import convert_path

    out = []
    stack=[(convert_path(where), '')]
    while stack:
        where,prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where,name)
            if (os.path.isdir(fn) and
                os.path.isfile(os.path.join(fn,'__init__.py'))
            ):
                out.append(prefix+name); stack.append((fn,prefix+name+'.'))
    for pat in exclude:
        from fnmatch import fnmatchcase
        out = [item for item in out if not fnmatchcase(item,pat)]
    return out

def generateDocs(options, outputDir):
    from epydoc.html import HTMLFormatter
    from epydoc.objdoc import DocMap, report_param_mismatches
    from epydoc.imports import import_module, find_modules
    from epydoc.objdoc import set_default_docformat

    if options.verbose:
        verbosity = 4
    else:
        verbosity = 1

    chandlerBin = os.getenv('CHANDLERBIN')

    targetDir = os.path.join(outputDir, 'api')

    if not os.path.isdir(targetDir):
        _mkdirs(targetDir)

      # This is the options dictionary
      # It is used by most of the epydoc routines and
      # the contents were determined by examining epydoc/gui.py
      # and epydoc/cli.py

    source_modules = ['samples/skeleton', 'Chandler.py', 'version.py', 
                      'PyICU', 
                      'chandlerdb', 'chandlerdb.item', 'chandlerdb.persistence', 
                      'chandlerdb.schema', 'chandlerdb.util']

    source_modules += find_modules('application')
    source_modules += find_modules('i18n')
    source_modules += find_modules('repository')
    source_modules += find_modules('tools')
    
    source_modules += find_packages('application', exclude=['*.tests'])
    source_modules += find_packages('i18n',        exclude=['*.tests'])
    source_modules += find_packages('repository',  exclude=['*.tests'])
    source_modules += find_packages('tools',       exclude=['*.tests'])

    parcels = find_packages('parcels', exclude=['*.tests'])

    map(schema.importString, parcels)
    for name,module in sys.modules.items():
        if module is not None and name.rsplit('.', 1)[0] in parcels:
            source_modules += [name]

    e_options = { 'target':       targetDir,
                  'verbosity':    verbosity,
                  'prj_name':     'Chandler',
                  'action':       'html',
                  'tests':        { 'basic': 1 },
                  'show_imports': 0,
                  'frames':       1,
                  'private':      0,
                  'debug':        0,
                  'docformat':    None,
                  'top':          None,
                  'inheritance':  "listed",
                  'alphabetical': 1,
                  'ignore_param_mismatch':   1,
                  'list_classes_separately': 0,
                  'modules': source_modules,
                 }

      # based on the code in epydoc's gui.py
      # with subtle changes made to make it work :)

    set_default_docformat('epytext')

    try:
        modules      = []
        module_names = e_options['modules']

          # walk thru list of modules and expand
          # any packages found
        for name in module_names[:]:
            if os.path.isdir(name):
                index       = module_names.index(name)
                new_modules = find_modules(name)

                if new_modules:
                    module_names[index:index+1] = new_modules
                elif options.verbose:
                    print 'Error: %s is not a package' % name

          # basic regex to exclude directories from consideration
        exc = re.compile(".*tests.*|.*scripts.*")

        for name in module_names:
            if exc.match(name):
                continue

            if options.verbose:
                print 'IMPORT: %s' % name

              # try importing the module and
              # add it to the list if successful
            try:
                module = import_module(name)

                if module not in modules:
                    modules.append(module)
                elif options.verbose:
                    print '  (duplicate)'
            except ImportError, e:
                if options.verbose:
                    print e

        if len(modules) == 0:
            print 'Error: no modules successfully loaded!'
            sys.exit(1)

        document_bases        = 1
        document_autogen_vars = 1
        inheritance_groups    = (e_options['inheritance'] == 'grouped')
        inherit_groups        = (e_options['inheritance'] != 'grouped')

          # let epydoc create an empty document map
        d = DocMap(verbosity, document_bases, document_autogen_vars,
                   inheritance_groups, inherit_groups)

          # walk the module list and let epydoc build the documentation
        for (module, num) in zip(modules, range(len(modules))):
            if options.verbose:
                print '\n***Building docs for %s***' % module.__name__

            try:
                d.add(module)
            except Exception, e:
                print "Internal Error: %s" % e
            except:
                print "Internal Error"

        if not e_options['ignore_param_mismatch']:
            if not report_param_mismatches(d):
                print '    (To supress these warnings, use --ignore-param-mismatch)'

        htmldoc  = HTMLFormatter(d, **e_options)
        numfiles = htmldoc.num_files()

        def progress_callback(path):
            (dir, file) = os.path.split(path)
            (root, d)   = os.path.split(dir)

            if d in ('public', 'private'):
                fname = os.path.join(d, file)
            else:
                fname = file

            if options.verbose:
                print '\n***Writing %s***' % fname

          # Write the documentation.
        print "\n***Saving to %s" % targetDir

        htmldoc.write(targetDir, progress_callback)

    except Exception, e:
        print 'Internal error: ', e
        raise
    except:
        raise


if __name__ == '__main__':
    options = Utility.initOptions()
    
    Utility.initLogging(options)

    if options.args:
        outputDir = options.args[0]
    else:
        outputDir = os.path.join(Utility.locateChandlerDirectory(), 'docs')

    if os.path.isfile('Chandler.py'):
        if not os.path.isdir(outputDir):
            _mkdirs(outputDir)

        generateModelDocs(options, outputDir)
        generateDocs(options, outputDir)
    else:
        print "Error: Currently gen_docs.py assumes it is running in the chandler/ directory"
