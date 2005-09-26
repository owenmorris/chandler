
# chandlerdb package

from chandlerdb.item.c import CItem, _install__doc__
import schema.c


_install__doc__(CItem.isNew, """
Tell whether this item is new.

A new item is defined as an item that was never committed to the repository.
@return: C{True} or C{False}
""")


_install__doc__(CItem.isDeleting, """
Tell whether this item is in the process of being deleted.

@return: C{True} or C{False}
""")

_install__doc__(CItem.isDeleted, """
Tell whether this item is deleted.

@return: C{True} or C{False}
""")

_install__doc__(CItem.isStale, """
Tell whether this item pointer is out of date.

A stale item pointer is defined as an item pointer that is no longer
valid. When an item is unloaded, the item pointer is marked
stale. The item pointer can be refreshed by reloading the item via the
L{find} method, passing it the item's C{uuid} obtained via the
L{itsUUID} property.

Stale items are encountered when item pointers are kept across
transaction boundaries. It is recommended to keep the item's
C{uuid} instead.

@return: C{True} or C{False}
""")

_install__doc__(CItem.isPinned, """
Tell whether this item is pinned.

A pinned item is not freed from memory or marked stale, until it
is un-pinned or deleted.

@return: C{True} or C{False}
""")

_install__doc__(CItem.isDirty, """
Tell whether this item was changed and needs to be committed.

@return: C{True} or C{False}
""")

_install__doc__(CItem.getAttributeAspect, """
Return the value for an attribute aspect.

An attribute aspect is one of an attribute's many attributes
described in the list below. All aspects are optional.

    - C{required}: C{True} if the attribute is required to have a
      value, C{False} otherwise, the default. This aspects takes a
      boolean value.
    - C{persisted}: C{True}, the default, if the attribute's value is
      persisted when the owning item is saved; C{False}
      otherwise. This aspect takes a boolean value.
    - C{cardinality}: C{single}, the default if the attribute is
      to have one single value, C{list} or C{dict}, if the attribute
      is to have a list or dictionary of values. This aspect takes a
      string value.
    - C{type}: a reference to the type item describing the type(s) of
      value(s) this attribute can store. By default, if this aspect
      is not set, an attribute can store value(s) of any type. This
      aspect takes an item of kind C{Type} as value.
    - C{defaultValue}: the value to return when there is no value
      set for this attribute. This default value is owned by the
      schema attribute item and is read-only when it is a collection
      or a Lob. Other mutable types, such as Structs, should be used
      with care as mutating a defaultValue causes it to appear
      changed by all items returning it. By default, an attribute
      has no default value. See C{initialValue}, C{inheritFrom} and
      C{redirectTo} below. This aspect takes any type of value.
    - C{initialValue}: similar to C{defaultValue} but the initial
      value is set as the value of the attribute the first time it is
      returned. A copy of the initial value is set when it is a
      collection. This aspect takes any type of value.
    - C{inheritFrom}: one or several attribute names chained
      together by periods naming attributes to recursively inherit a
      value from. When several names are used, all but the last name
      are expected to name attributes containing a reference to the
      next item to inherit from by applying the next name. This
      aspect takes a string value.
    - C{redirectTo}: one or several attribute names chained
      together by periods naming attributes to recursively obtain a
      value or aspect value from or set a value to. When several
      names are used, all but the last name are expected to name
      attributes containing a reference to the next item to redirect
      to by applying the next name. This aspect takes a string
      value.
    - C{otherName}: for bi-directional reference attributes, this
      aspect names the attribute used to attach the other endpoint
      on the other item, ie the referenced item. This is the aspect
      that determines whether the attribute stored bi-directional
      references to items. This aspect takes a string value.
    - C{copyPolicy}: when an item is copied this policy defines
      what happens to items that are referenced by this
      attribute. Possible C{copyPolicy} values are:
        - C{remove}, the default. The reference is not copied.
        - C{copy}, the reference is copied.
        - C{cascade}, the referenced item is copied recursively and
          a reference to this copy is set.
      This aspect takes a string value.
    - C{deletePolicy}: when an item is deleted this policy defines
      what happens to items that are referenced by this
      attribute. Possible C{deletePolicy} values are:
        - C{remove}, the default.
        - C{cascade}, which causes the referenced item(s) to get
          deleted as well. See C{countPolicy} below.
      This aspect takes a string value.
    - C{countPolicy}: when an attribute's C{deletePolicy} is
      C{cascade} this aspect can be used to modify the delete
      behaviour to only delete the referenced item if its reference
      count is 0. The reference count of an item is defined by the
      total number of references it holds in attributes where the
      C{countPolicy} is set to C{count}. By default, an attribute's
      C{countPolicy} is C{none}. This aspect takes a string value.

If the attribute's C{redirectTo} aspect is set, this method is
redirected just like C{getAttributeValue}.

If the attribute is not defined for the item's kind,
a subclass of C{AttributeError} is raised.

@param name: the name of the attribute being queried
@type name: a string
@param aspect: the name of the aspect being queried
@type aspect: a string
@param kwds: optional keywords of which only C{default} is
supported and used to return a default value for an aspect that has
no value set for the attribute.
@return: a value
""")

_install__doc__(CItem.getDirty, """
Return the dirty flags currently set on this item.

@return: an integer
""")

_install__doc__(CItem.itsName, """
Return this item's name.

The item name is used to lookup an item in its parent
container and construct the item's path in the repository.
An item may be renamed by setting this property.

The name of an item must be unique among all its siblings.
""")

_install__doc__(CItem.itsUUID, """
Return the Universally Unique ID for this item.

The UUID for an item is generated when the item is
first created and never changes. This UUID is valid
for the life of the item.

The UUID is a 128 bit number intended to be unique in
the entire universe and is implemented as specified
in the IETF's U{UUID draft
<www.ics.uci.edu/pub/ietf/webdav/uuid-guid/draft-leach-uuids-guids-01.txt>}
spec.
""")

_install__doc__(CItem.itsPath, """
Return the path to this item relative to its repository.

A path is a C{/} separated sequence of item names.
""")

_install__doc__(CItem.itsParent, """
Return this item's parent.

An item may be moved by setting this property.
""")

_install__doc__(CItem.itsRoot, """
Return this item's repository root.

A repository root is a direct child of the repository.
All single-slash rooted paths are expressed relative
to this root when used with this item.
""")

_install__doc__(CItem.itsView, """
Return this item's repository view.

The item's repository view is defined as the item's root's parent.
""")

_install__doc__(CItem.itsKind, """
Return or set this item's kind.

When setting an item's kind, only the values for
attributes common to both current and new kind are
retained. After the new kind is set, its attributes'
optional L{initial values<getAttributeAspect>} are
set for attributes for which there is no value on the
item. Setting an item's kind to C{None} clears all its values.
""")
