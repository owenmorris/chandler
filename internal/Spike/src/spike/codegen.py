"""Repository -> Python code generation utilities (see codegen.txt for docs)"""

import sys

cardinalities = {
    'single':'One', 'list':'Many', 'dict':'Mapping'
}

def generateClass(kind,stream=None):
    """Generate a class skeleton from a repository kind"""

    if stream is None:
        stream = sys.stdout
    if kind.superKinds:
        bases = '(%s)' % ','.join([base.itsName for base in kind.superKinds])
    else:
        bases = ''

    print >>stream, "class %s%s:" % (kind.itsName, bases)

    for attr in kind.attributes:
        generateAttribute(attr,stream)


def generateAttribute(attr,stream=None):
    """Generate an attribute definition from a repository attribute item"""

    if stream is None:
        stream = sys.stdout

    cardinality = cardinalities[attr.cardinality]

    stream.write("    %s = schema.%s(" % (attr.itsName, cardinality))

    if hasattr(attr,'type'):
        stream.write(attr.type.itsName)
    else:
        stream.write('object')  # XXX

    if attr.required:
        stream.write(', required=True')

    stream.write(")\n")

