
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


def main():
    from distutils.core import setup, Extension
    setup(name='UUIDext', ext_modules=[Extension('UUIDext', sources=['uuid.c',
     'pyuuid.c'])])

if __name__ == "__main__":
    main()
