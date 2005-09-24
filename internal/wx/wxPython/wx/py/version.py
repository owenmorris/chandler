"""Provides an object representing the current 'version' or 'release'
of Py as a whole.  Individual classes, such as the shell, filling and
interpreter, each have a revision property based on the CVS Revision."""

__author__ = "Patrick K. O'Brien <pobrien@orbtech.com>"
__cvsid__ = "$Id: version.py,v 1.5 2004/01/25 23:37:41 PKO Exp $"
__revision__ = "$Revision: 1.5 $"[11:-2]

VERSION = '0.9.4'
