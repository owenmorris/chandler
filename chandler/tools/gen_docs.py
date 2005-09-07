import os, sys, re

def generateDocs(outputDir=None, verbose=False):
    if verbose:
        verbosity = 4
    else:
        verbosity = 1

    if sys.platform == 'cygwin':
        chandlerdb = 'release/bin/Lib/site-packages/chandlerdb'
        queryparser = 'release/bin/Lib/site-packages/QueryParser.py'
    elif sys.platform == 'darwin':
        chandlerdb = 'release/Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4/site-packages/chandlerdb'
        queryparser = 'release/Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4/site-packages/QueryParser.py'
    else:
        chandlerdb = 'release/lib/python2.4/site-packages/chandlerdb'
        queryparser = 'release/lib/python2.4/site-packages/QueryParser.py'

      # This is the options dictionary
      # It is used by most of the epydoc routines and
      # the contents were determined by examining epydoc/gui.py
      # and epydoc/cli.py

    options = { 'target':       outputDir,
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
                'modules': ['application',
                            'crypto',
                            'i18n',
                            'parcels/core',
                            'parcels/feeds',
                            'parcels/osaf',
                            'parcels/osaf/app',
                            'parcels/osaf/examples',
                            'parcels/osaf/framework',
                            'parcels/osaf/mail',
                            'parcels/osaf/pim',
                            'parcels/osaf/servlets',
                            'parcels/osaf/sharing',
                            'parcels/osaf/tests',
                            'parcels/osaf/views',
                            'parcels/photos',
                            'repository',
                            'samples/skeleton',
                            'tools',
                            'util',
                            'Chandler.py',
                            'version.py',
                            chandlerdb, # This comes from internal
                            queryparser # This comes from external
                           ],
               }

      # based on the code in epydoc's gui.py
      # with subtle changes made to make it work :)

    from epydoc.html import HTMLFormatter
    from epydoc.objdoc import DocMap, report_param_mismatches
    from epydoc.imports import import_module, find_modules
    from epydoc.objdoc import set_default_docformat

    set_default_docformat('epytext')

    try:
        modules      = []
        module_names = options['modules']

          # walk thru list of modules and expand
          # any packages found
        for name in module_names[:]:
            if os.path.isdir(name):
                index       = module_names.index(name)
                new_modules = find_modules(name)

                if new_modules:
                    module_names[index:index+1] = new_modules
                elif verbose:
                    print 'Error: %s is not a package' % name

          # basic regex to exclude directories from consideration
        exc = re.compile(".*tests.*|.*scripts.*")

        for name in module_names:
            if exc.match(name):
                continue

            if verbose:
                print 'IMPORT: %s' % name

              # try importing the module and
              # add it to the list if successful
            try:
                module = import_module(name)

                if module not in modules:
                    modules.append(module)
                elif verbose:
                    print '  (duplicate)'
            except ImportError, e:
                if verbose >= 0:
                    print e

        if len(modules) == 0:
            print 'Error: no modules successfully loaded!'
            sys.exit(1)

        document_bases        = 1
        document_autogen_vars = 1
        inheritance_groups    = (options['inheritance'] == 'grouped')
        inherit_groups        = (options['inheritance'] != 'grouped')

          # let epydoc create an empty document map
        d = DocMap(verbosity, document_bases, document_autogen_vars,
                   inheritance_groups, inherit_groups)

          # walk the module list and let epydoc build the documentation
        for (module, num) in zip(modules, range(len(modules))):
            if verbose:
                print '\n***Building docs for %s***' % module.__name__

            try:
                d.add(module)
            except Exception, e:
                print "Internal Error: %s" % e
            except:
                print "Internal Error"

        if not options['ignore_param_mismatch']:
            if not report_param_mismatches(d):
                print '    (To supress these warnings, use --ignore-param-mismatch)'

        htmldoc  = HTMLFormatter(d, **options)
        numfiles = htmldoc.num_files()

        def progress_callback(path, numfiles=numfiles, progress=None, cancel=None, num=[1]):
            (dir, file) = os.path.split(path)
            (root, d)   = os.path.split(dir)

            if d in ('public', 'private'):
                fname = os.path.join(d, file)
            else:
                fname = file

            if verbose:
                print '\n***Writing %s***' % fname

          # Write the documentation.
        print "\n***Saving to %s" % outputDir

        htmldoc.write(outputDir, progress_callback)

    except Exception, e:
        print 'Internal error: ', e
        raise
    except:
        raise

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options] output_directory")
    parser.add_option("-q", "--quiet",
        action="store_false", dest="verbose", default=True,
        help="don't display the verbose information about modules being documented"
    )

    (options, args) = parser.parse_args()

    if not args:
        outputDir = os.path.join(os.getenv('CHANDLERHOME'), 'docs', 'api')

        print "Output directory not specified - defaulting to %s" % outputDir
    else:
        outputDir = args[0]

    generateDocs(outputDir, options.verbose)
