_version = { 'release':    '0.7alpha5',
             'build':      '.dev',
             'checkpoint': None,
             'revision':   None,
           }

_template = '%(release)s'

  # the checkpoint and release information is added
  # to the version string *only* if we are doing one of:
  #     continuous build        build = '.dev'
  #                             checkpoint = None
  #     checkpoint build        build = '.dev'
  #                             checkpoint value set to YYYYMMDD
  #     Milestone or Release    build = ''
  #                             checkpoint = None
  #                             revision = None

if len(_version['build']) > 0:
    _template += '%(build)s'

    import os

    try:
        chandlerDir = os.path.dirname(__file__)
    except:
        chandlerDir = '.'

        # pull the .svn/entries file from the directory where version.py resides
        # and read the value for the revision property

    svnfile = os.path.join(chandlerDir, '.svn', 'entries')

    if os.path.isfile(svnfile):
        for line in file(svnfile):
            items = line.split('=')

            if len(items) == 2:
                item, value = items

                if item.strip().lower() == 'revision':
                    _version['revision'] = value[:-1].strip('">/')

    if _version['revision'] is not None:
        _template += '-r%(revision)s'

    if _version['checkpoint'] is not None:
        _template += '-checkpoint%(checkpoint)s'

release    = _version['release']
build      = '%s' % _version['build']
checkpoint = '%s' % _version['checkpoint']
revision   = '%s' % _version['revision']
version    = _template % _version


