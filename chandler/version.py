_version = { 'release':    '0.7',
             'build':      '.dev',
             'checkpoint': None,
             'revision':   None,
           }

#!#!#!#!# <-- used by build_lib.py to mark end of _version def
# Note: do not edit or change anything above this comment block
#       as it can/will be replaced during the build process
#
#     continuous build        build = '.dev'
#                             checkpoint = YYYYMMDDHHMMSS
#                             revision set by caller
#
#     checkpoint build        build = '.dev'
#                             checkpoint value set to YYYYMMDD
#                             revision set by caller
#
#     Milestone or Release    build = ''
#                             checkpoint = None
#                             revision = None

_template = '%(release)s'

if len(_version['build']) > 0:
    _template += '%(build)s'

    # dig into the file system to figure out what the revision number is
    # but only if the build system hasn't provided one
    if _version['revision'] is None:
        import os

        try:
            chandlerDir = os.path.dirname(__file__)
        except:
            chandlerDir = '.'

            # pull the .svn/entries file from the directory where version.py resides
            # and read the value for the revision property

        svnfile = os.path.join(chandlerDir, '.svn', 'entries')

        if os.path.isfile(svnfile):
            # svn 1.3
            for line in file(svnfile):
                items = line.split('=')

                if len(items) == 2:
                    item, value = items

                    if item.strip().lower() == 'revision':
                        _version['revision'] = value[:-1].strip('">/')

            # svn 1.4
            if _version['revision'] == None:
                revisions = []
                for line in file(svnfile):
                    try:
                        revisions.append(long(line))
                    except ValueError:
                        pass
                revisions.sort()
                _version['revision'] = str(revisions[-1])

    if _version['revision'] is not None:
        _template += '-r%(revision)s'

    if _version['checkpoint'] is not None:
        # continuous builds do not use -checkpoint text
        if len(_version['checkpoint']) > 8:
            _template += '-%(checkpoint)s'
        else:
            _template += '-checkpoint%(checkpoint)s'

release    = _version['release']
build      = '%s' % _version['build']
checkpoint = '%s' % _version['checkpoint']
revision   = '%s' % _version['revision']
version    = _template % _version

