
__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class LocalizableString(object):
    """
    This class is just a stand-in. If more fields are added and they need to
    be persisted, the LocalizableString.type file needs to be modified
    accordingly.

    The reason for this class, is solely to serve as a python implementation
    type for Chandler values of the LocalizableString schema type.

    It can, of course, have any number of methods and implementation
    details. Only persistent fields (python attributes) need to be described
    in the schema type file, LocalizableString.type.

    If custom persistence needs to be implemented, that is the persisting of
    values of this type needs to be customized with regards to the default
    implementation on the Struct core schema type item, then a subclass of
    repository.schema.Types.Struct needs to be implemented with the relevant
    customization and the LocalizableString schema type item needs to be of
    that class. (See the core schema Date type as an example).
    """

    pass
