# XXX The compiler you are using
CC=	 	gcc

# XXX Top of the build tree and source tree
blddir=		../../../../python
srcdir=		../../../../python

# Python version
VERSION=	2.3

# Compiler flags
OPT=		-g
INCLUDES=	-I$(srcdir)/Include -I$(blddir)
CFLAGS=		$(OPT)
CPPFLAGS=	$(INCLUDES)

# The Python library
LIBPYTHON=	$(blddir)/libpython$(VERSION).a

# XXX edit LIBS (in particular) to match $(blddir)/Modules/Makefile
LIBS=		-lnsl -ldl -lreadline -ltermcap -lieee -lpthread -lutil
LDFLAGS=	-Xlinker -export-dynamic
SYSLIBS=	-lm
MODLIBS=	
ALLLIBS=	$(LIBPYTHON) $(MODLIBS) $(LIBS) $(SYSLIBS)

all:		chandler chandler_bin

chandler:	chandler.o
		$(CC) $(CFLAGS) $(LDFLAGS) chandler.o -o chandler

chandler_bin:	chandler_bin.o
		$(CC) $(CFLAGS) $(LDFLAGS) chandler_bin.o $(ALLLIBS) -o chandler_bin

clean:
		-rm -f *.o core 

clobber:	clean
		-rm -f *~ @* '#'* chandler chandler_bin

realclean:	clobber
