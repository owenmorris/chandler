
import os, sys, hardhatlib

info = {
        'name': 'repository',
        'root': '../..',
       }

dependencies = ()


def build(buildenv):

    # Build API documentation into api subdirectory (except dos windows)

    if buildenv['os'] != 'win' or sys.platform == 'cygwin':
        hardhatlib.epydoc(buildenv, info['name'], 'Generating API docs',
                          '-o api -v -n chandlerdb',
                          '--no-private', '--inheritance listed',
                          'item', 'persistence', 'schema', 'util')


def clean(buildenv):
    pass


def run(buildenv):
    hardhatlib.log(buildenv, hardhatlib.HARDHAT_WARNING, info['name'], 
                   "Nothing to run")
