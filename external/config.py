
import os

def configure_distutils(sitePath, binPath):

    for name in os.listdir(sitePath):
        if name.startswith('distutils.'):
            os.remove(os.path.join(sitePath, name))

    import distutils

    py = file(os.path.join(sitePath, 'distutils.py'), 'w')
    print >>py, "__path__=['%s']" %(os.path.dirname(distutils.__file__))
    print >>py, "from distutils.__init__ import __version__, __revision__, __doc__"
    py.close()

    cfg = file(os.path.join(sitePath, 'distutils.cfg'), 'w')
    print >>cfg, "[install]"
    print >>cfg, "install_lib=%s" %(sitePath)
    print >>cfg, "install_data=%s" %(sitePath)
    print >>cfg, "install_scripts=%s" %(binPath)
    cfg.close()


if __name__ == "__main__":
    import sys
    configure_distutils(*sys.argv[1:])
