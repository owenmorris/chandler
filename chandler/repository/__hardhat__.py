
import os, sys, hardhatlib

info = {
        'name': 'repository',
        'root': '../..',
       }

dependencies = (
               )


def build(buildenv):

    # Build UUID extension and install it

    os.chdir(os.path.join("util", "ext"))

    if buildenv['version'] == 'release':
        hardhatlib.executeCommand(buildenv, info['name'],
                                  [buildenv['python'], 'setup.py', 'build',
                                   '--build-base=build_release', 'install'],
                                  "Building and installing UUIDext release")
    elif buildenv['version'] == 'debug':
        hardhatlib.executeCommand(buildenv, info['name'],
                                  [buildenv['python_d'], 'setup.py', 'build',
                                   '--build-base=build_debug', '--debug',
                                   'install', '--force'],
                                  "Building and installing UUIDext debug")

    os.chdir("../..")

    # Build API documentation into api subdirectory (except dos windows)

    if buildenv['os'] != 'win' or sys.platform == 'cygwin':
        hardhatlib.epydoc(buildenv, info['name'], 'Generating API docs',
                          '-o api -v -n chandlerdb',
                          '--no-private', 'item', 'schema', 'util')


def clean(buildenv):

    os.chdir(os.path.join("util", "ext"))

    if buildenv['version'] == 'release':
        if os.path.exists("build_release"):
            hardhatlib.rmdir_recursive("build_release")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
                           info['name'], "Removed UUIDext build_release")
    elif buildenv['version'] == 'debug':
        if os.path.exists("build_debug"):
            hardhatlib.rmdir_recursive("build_debug")
            hardhatlib.log(buildenv, hardhatlib.HARDHAT_MESSAGE, 
                           info['name'], "Removed build_debug")

    os.chdir("../..")


def run(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_WARNING, info['name'], 
                   "Nothing to run")
