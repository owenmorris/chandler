
include ../../Makefile.inc

RELVER=0.3-1
LAUNCHERS=$(INTERNAL)/launchers

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

build:
	mkdir -p $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler.c -o $(BUILD)/chandler
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler_bin.c $(ALLLIBS) -o $(BUILD)/chandler_bin
	cp $(BUILD)/chandler $(BUILD_ROOT)/$(SNAP)
	cp $(BUILD)/chandler_bin $(BUILD_ROOT)/$(SNAP)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERS)/launchers-$(SNAP)-$(RELVER).tar.gz \
          $(SNAP)/chandler $(SNAP)/chandler_bin

clean:
	rm -rf $(BUILD)

upload: launchers-$(SNAP)-$(RELVER).tar.gz
	scp launchers-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
