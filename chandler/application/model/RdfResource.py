#!bin/env python

"""Base classes for RDF resources in Chandler
"""

from application.persist import Persist

import sys

if sys.version[0:3] == '2.3':
    class RdfResource(Persist.Persistent):
	def __init__(self):
	    pass
else:
    class RdfResource(object, Persist.Persistent):
	def __init__(self):
	    pass
    
