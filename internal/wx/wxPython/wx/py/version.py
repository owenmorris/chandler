"""Provides an object representing the current 'version' or 'release'
of Py as a whole.  Individual classes, such as the shell, filling and
interpreter, each have a revision property based on the CVS Revision."""

__author__ = "Patrick K. O'Brien <pobrien@orbtech.com>"
__cvsid__ = "$Id: version.py 5166 2005-04-29 01:36:53Z davids $"
__revision__ = "$Revision: 5166 $"[11:-2]

VERSION = '0.9.4'
