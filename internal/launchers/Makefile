
include ../Makefile.inc

RELVER=0.3-3
LAUNCHERS=$(INTERNAL)/launchers

BUILD=build_$(SNAP)

# ifeq ($(DEBUG),1)
#     DEBUG=$DEBUG
# else
#     undef DEBUG
# endif

ifeq ($(PLATFORM),windows)
    SCRIPT_EXTENTION=".bat"
else
    SCRIPT_EXTENTION=
endif

ifeq ($(OS),Darwin)

LAUNCHER_FILES=
LIB_FILES=

build:
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)

endif

ifeq ($(OS),Cygwin)

LAUNCHER_FILES=$(SNAP)/chandler.exe
LIB_FILES=$(SNAP)/bin/ms*dll

ARCHIVE: $(LAUNCHERS)/win/

build:
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
	cd $(LAUNCHERS)/win; \
	make
endif

ifeq ($(OS),Linux)

LAUNCHER_FILES=$(SNAP)/chandler $(SNAP)/lib/chandler_bin
LIB_FILES=

ARCHIVE: $(LAUNCHERS)/linux/

build:
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
	cd $(LAUNCHERS)/linux; \
	make

endif

#  common to all platforms

MANIFEST=$(SNAP)/Run* \
         $(LAUNCHER_FILES) \
         $(LIB_FILES)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERS)/Launchers-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(BUILD_ROOT)/../chandler -xvf -

clean:
	rm -rf $(BUILD)

upload: Launchers-$(SNAP)-$(RELVER).tar.gz
	scp Launchers-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
