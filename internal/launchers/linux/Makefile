
include ../../Makefile.inc


BUILD=build_$(SNAP)

CC=	 	gcc

# Compiler flags
ifeq ($(DEBUG),1)
    CFLAGS=		-g -DDEBUGMODE=1
else
    CFLAGS=		-O
endif

INCLUDES=	-I$(BUILD_ROOT)/$(SNAP)/include/python2.3
LIBPYTHON=	$(BUILD_ROOT)/$(SNAP)/lib/python2.3/config/libpython2.3.a

# XXX edit LIBS (in particular) to match Modules/Makefile
LIBS=		-lnsl -ldl -lieee -lpthread -lutil
LDFLAGS=	-Xlinker -export-dynamic
SYSLIBS=	-lm
MODLIBS=	
ALLLIBS=	$(LIBPYTHON) $(MODLIBS) $(LIBS) $(SYSLIBS)

ifeq ($(SNAP),debug)
build:
	mkdir -p $(BUILD)/lib
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler.c -o $(BUILD)/chandlerDebug
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler_bin.c $(ALLLIBS) -o $(BUILD)/lib/chandler_bin
	cp $(BUILD)/chandlerDebug $(BUILD_ROOT)
	cp $(BUILD)/lib/chandler_bin $(BUILD_ROOT)/$(SNAP)/lib
else
build:
	mkdir -p $(BUILD)/lib
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler.c -o $(BUILD)/chandler
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler_bin.c $(ALLLIBS) -o $(BUILD)/lib/chandler_bin
	cp $(BUILD)/chandler $(BUILD_ROOT)
	cp $(BUILD)/lib/chandler_bin $(BUILD_ROOT)/$(SNAP)/lib
endif


clean:
	rm -rf $(BUILD)
