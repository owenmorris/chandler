
RELVER=0.9-$(BRANCH_REV_PREFIX)2
LAUNCHERS=$(INTERNAL)/launchers
SRC=$(LAUNCHERS)
BUILD=build_$(SNAP)
TARBALL=Launchers-$(SNAP)-$(RELVER).tar.gz

include ../Makefile.inc

ifeq ($(PLATFORM),windows)
    SCRIPT_EXTENTION=".bat"
else
    SCRIPT_EXTENTION=
endif

ifeq ($(OS),Darwin)

LAUNCHER_FILES=
LIB_FILES=

clean:
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

build:
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)

endif

ifeq ($(OS),Cygwin)

ifeq ($(DEBUG),1)
LAUNCHER_FILES=./chandlerDebug.exe $(SNAP)/bin/chandler.exe
else
LAUNCHER_FILES=./chandler.exe $(SNAP)/bin/chandler.exe
endif

LIB_FILES=$(SNAP)/bin/ms*dll

ARCHIVE: $(LAUNCHERS)/win/

clean:
	$(MAKE) -C win -k DEBUG=$(DEBUG) clean
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

build: 
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
	$(MAKE) -C $(LAUNCHERS)/win

endif

ifeq ($(OS),Linux)

ifeq ($(DEBUG),1)
LAUNCHER=chandlerDebug
LAUNCHER_FILES=./$(LAUNCHER)
else
LAUNCHER=chandler
LAUNCHER_FILES=./$(LAUNCHER)
endif
LIB_FILES=

ARCHIVE: $(LAUNCHERS)/linux/

clean:
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

build:
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/linux/$(LAUNCHER) $(BUILD_ROOT)/$(LAUNCHER)

endif

#  common to all platforms

MANIFEST=$(SNAP)/Run* \
         $(LAUNCHER_FILES) \
         $(LIB_FILES)

snap: strip
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERS)/$(TARBALL) $(MANIFEST)

install:
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

realclean: clean
	rm -f Launchers-debug-*.tar.gz* Launchers-release-*.tar.gz*

upload: $(TARBALL)
	scp $(TARBALL) $(UPLOAD)
