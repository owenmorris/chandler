
from distutils.core import setup, Extension
setup(name='UUIDext', ext_modules=[Extension('UUIDext', sources=['uuid.c',
                                                                 'pyuuid.c'])])
