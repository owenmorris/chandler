_version = { 'release':    '1.0',
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

# Increment this value whenever the schema changes, and replace the comment
# with your name (and some helpful text). The comment's really there just to
# cause Subversion to warn you of a conflict when you update, in case someone 
# else changes it at the same time you do (that's why it's on the same line).
app_version = "499" # jeffrey: Sort LATER by date then last-triaged



_template = '%(release)s'

if _version['build']:
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
            if _version['revision'] is None:
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
