
include ../../Makefile.inc

RELVER=0.3-1
LAUNCHERLINUX=$(INTERNAL)/launchers/linux

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
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler.c -o chandler
	$(CC) $(CFLAGS) $(LDFLAGS) $(INCLUDES) chandler_bin.c $(ALLLIBS) -o chandler_bin
	cp chandler $(BUILD_ROOT)/$(SNAP)
	cp chandler_bin $(BUILD_ROOT)/$(SNAP)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERLINUX)/launcherlinux-$(SNAP)-$(RELVER).tar.gz \
          $(SNAP)/chandler $(SNAP)/chandler_bin

clean:
	rm -rf $(BUILD)

upload: UUIDext-$(SNAP)-$(RELVER).tar.gz
	scp UUIDext-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
