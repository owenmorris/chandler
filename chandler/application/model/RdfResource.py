#!bin/env python

"""Base classes for RDF resources in Chandler
"""

from Persistence import Persistent

import sys

if sys.version[0:3] == '2.3':
    class RdfResource(Persistent):
        def __init__(self):
            pass
else:
    class RdfResource(object, Persistent):
        def __init__(self):
            pass
