# XXX The compiler you are using
CC=	 	gcc

# Compiler flags
ifeq ($(DEBUG),1)
    CFLAGS=		-g -DDEBUGMODE=1
    INCLUDES=	-I../../../../debug/include/python2.3
    LIBPYTHON=	../../../../debug/lib/python2.3/config/libpython2.3.a
else
    INCLUDES=	-I../../../../release/include/python2.3
    LIBPYTHON=	../../../../release/lib/python2.3/config/libpython2.3.a
    CFLAGS=		-O
endif
CPPFLAGS=	$(INCLUDES)


# XXX edit LIBS (in particular) to match Modules/Makefile
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
