import os, hardhatlib


info = {
        'name':'wxWindows-2.5.1.5',
        'root':'../..',
        'path':'internal/wxPython-2.5',
       }

dependencies = (
                'python',
               )


def build(buildenv):

    version = buildenv['version']

    if buildenv['os'] in ('osx', 'posix'):


        # Create the build directory

        buildDir = os.path.abspath("build_%s" % version)
        if os.access(buildDir, os.F_OK):
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], 
             "Temporary build directory exists: " + buildDir)
        else:
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], 
             "Temporary build directory doesn't exist; creating: " + \
              buildDir)
            os.mkdir(buildDir)
        os.chdir(buildDir)

        # Prepare the wxWidgets command line

        buildOptions = [
         buildenv['sh'], 
         '../configure', 
         '--prefix=%s' % os.path.join(buildenv['root'],version),
         '--disable-monolithic',
         '--enable-geometry',
         '--enable-sound',
         '--with-sdl',
         '--enable-display',
        ]

        if version == "debug":
            buildOptions.append("--enable-debug")
        else:
            buildOptions.append("--enable-optimized")

        if buildenv['os'] == "osx":
            buildOptions.append("--with-mac")
            buildOptions.append("--with-opengl")

        if buildenv['os'] == "posix":
            buildOptions.append("--with-gtk")
            buildOptions.append("--enable-gtk2")
            buildOptions.append("--enable-unicode")

        # Configure

        if os.access('Makefile', os.F_OK):
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], "Already configured")
        else:
            hardhatlib.executeCommand(buildenv, info['name'],
             buildOptions,
             "Configuring wxWindows %s" % version)

        # Make

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make']], "Making wxWindows")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/gizmos'], "Making gizmos")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'],
          '-Ccontrib/src/ogl',
          'CXXFLAGS="-DwxUSE_DEPRECATED=0"',
          ], "Making ogl")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/stc'], "Making stc")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/xrc'], "Making xrc")

        # Install

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], 'install'], "Installing wxWindows")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/gizmos', 'install'],
         "Installing gizmos")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/ogl', 'install'],
         "Installing ogl")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/stc', 'install'], 
         "Installing stc")

        hardhatlib.executeCommand(buildenv, info['name'],
         [buildenv['make'], '-Ccontrib/src/xrc', 'install'], 
         "Installing xrc")


        # wxPython

        if version == "debug":
            python = buildenv['python_d']
        else:
            python = buildenv['python']

        os.chdir("../wxPython")

        buildOptions = [
         python,
         'setup.py',
         'FINAL=1',
         'BUILD_OGL=0',
         'BUILD_GLCANVAS=0',
         'BUILD_BASE=build_%s' % version,
         'WX_CONFIG='+buildenv['root']+'/%s/bin/wx-config' % version,
        ]

        if buildenv['os'] == "posix":
            buildOptions.append("WXPORT=gtk2")
            buildOptions.append("UNICODE=1")

        buildOptions.append("build")
        if version == "debug":
            buildOptions.append("--debug")

        buildOptions.append("install")

        hardhatlib.executeCommand(buildenv, info['name'], buildOptions,
         "Building and Installing wxPython")


    # Windows

    if buildenv['os'] == 'win':

        hardhatlib.executeCommand( buildenv, info['name'],
         [buildenv['compiler'], 
         "build/msw/msw.sln",
         "/build",
         version.capitalize(),
         "/out",
         "output.txt"],
         "Building %s %s" % (info['name'], version),
         0, "output.txt")

        os.putenv('WXWIN', buildenv['root_dos'] + "\\..\\..\\internal\\wxPython-2.5")

        if version == 'release':
            destination = os.path.join (buildenv['pythonlibdir'], 'site-packages', 'wx')
            hardhatlib.copyFiles('lib/vc_dll', destination, ['*251_*.dll'])

            os.chdir("wxPython")
            hardhatlib.executeCommand (buildenv,
                                       info['name'],
                                       [buildenv['python'],
                                        'setup.py',
                                        'FINAL=1',
                                        'BUILD_BASE=build_release',
                                        'build', 
                                        'install'],
                                       "Building wxPython")

            # _*.pyd also copies _*_d.pyd, which is unnecessary, however, the
            # files that should have been created are _*.pyc, so when we fix that
            # we should change '_*.pyd' to '_*.pyc' in the following line
            hardhatlib.copyFiles('wx', destination, ['_*.pyd'])

        elif version == 'debug':
            destination = os.path.join (buildenv['pythonlibdir_d'], 'site-packages', 'wx')
            hardhatlib.copyFiles('lib/vc_dll', destination, ['*251d_*.dll'])

            os.chdir("wxPython")
            hardhatlib.executeCommand (buildenv,
                                       info['name'],
                                       [buildenv['python_d'],
                                        'setup.py',
                                        'FINAL=1',
                                        'BUILD_BASE=build_debug',
                                        'build',
                                        '--debug',
                                        'install'],
                                       "Building wxPython")

            hardhatlib.copyFiles('wx', destination, ['_*_d.pyd'])

def clean(buildenv):

    version = buildenv['version']

    if buildenv['os'] == 'posix':

        buildDir=os.path.abspath("build_%s" % version)
 
        if os.access(buildDir, os.F_OK):
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], 
             "Removing temporary build directory: " + buildDir)
            hardhatlib.rmdir_recursive(buildDir)


    if buildenv['os'] == 'osx':

        buildDir=os.path.abspath("build_%s" % version)

        if os.access(buildDir, os.F_OK):
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
             info['name'], 
             "Removing temporary build directory: " + buildDir)
            hardhatlib.rmdir_recursive(buildDir)


    if buildenv['os'] == 'win':

        hardhatlib.executeCommand( buildenv, info['name'],
         [buildenv['compiler'], 
         "build/msw/msw.sln",
         "/clean",
         version.capitalize(),
         "/out",
         "output.txt"],
         "Cleaning %s %s" % (info['name'], version),
         0, "output.txt")
         
         
        os.putenv('WXWIN', buildenv['root_dos'] + "\\..\\..\\internal\\wx\\wxPython-2.5")

        os.chdir("wxPython")

        if version == 'release':

            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['python'], 'setup.py', 'BUILD_BASE=build_release',
             'clean', '--all'], "Cleaning wxPython")

        elif version == 'debug':

            hardhatlib.executeCommand( buildenv, info['name'],
             [buildenv['python_d'], 'setup.py', 'BUILD_BASE=build_debug',
             'clean', '--all'], "Cleaning wxPython")


def run(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_WARNING, info['name'], 
     "Nothing to run")

