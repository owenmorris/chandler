__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
Set of globals for easy access to things

These are initialized by Application so don't try to use them
before it has been initialized.

If you are not Application DO NOT SET THESE

Check with someone before adding new things here.
"""

__all__ = [ 'app', 'repository' ]

# The wxApplication object
app = None

# The local repository
repository = None
