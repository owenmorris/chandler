
RELVER=0.9-$(BRANCH_REV_PREFIX)32
LAUNCHERS=$(INTERNAL)/launchers
SRC=$(LAUNCHERS)
BUILD=build_$(SNAP)
TARBALL=Launchers-$(SNAP)-$(RELVER).tar.gz

include ../Makefile.inc

.PHONY: scripts

ifeq ($(OS),Darwin)

SCRIPT_EXTENSION=
LIB_FILES=

ifneq ($(OS_MAJOR_VER),9)

LAUNCHER_FILES=

else

LAUNCHER_FILES=$(BUILD_ROOT)/$(SNAP)/Chandler

build:
	$(MAKE) -C $(LAUNCHERS)/osx build

endif

build: scripts

clean:
	make -C osx clean
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

endif

ifeq ($(OS),Cygwin)

SCRIPT_EXTENSION=".bat"
LIB_FILES=$(SNAP)/bin/ms*dll

ifeq ($(DEBUG),1)
LAUNCHER_FILES=./chandlerDebug.exe
else
LAUNCHER_FILES=./chandler.exe
endif

ARCHIVE: $(LAUNCHERS)/win/

build: scripts
	$(MAKE) -C $(LAUNCHERS)/win

clean:
	$(MAKE) -C win -k DEBUG=$(DEBUG) clean
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

endif

ifeq ($(OS),Linux)

SCRIPT_EXTENSION=
LIB_FILES=

ifeq ($(DEBUG),1)
LAUNCHER=chandlerDebug
LAUNCHER_FILES=./$(LAUNCHER)
else
LAUNCHER=chandler
LAUNCHER_FILES=./$(LAUNCHER)
endif

ARCHIVE: $(LAUNCHERS)/linux/

clean:
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst

build: scripts
	cp $(LAUNCHERS)/linux/$(LAUNCHER) $(BUILD_ROOT)/$(LAUNCHER)

endif

#  common to all platforms

MANIFEST=$(SNAP)/RunPython$(SCRIPT_EXTENSION) \
         $(SNAP)/InstallPlugin$(SCRIPT_EXTENSION) \
         $(LAUNCHER_FILES) \
         $(LIB_FILES)

scripts:
	cp -p $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENSION)
	cp -p $(LAUNCHERS)/scripts/InstallPlugin.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/InstallPlugin$(SCRIPT_EXTENSION)

snap: strip
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERS)/$(TARBALL) $(MANIFEST)

install:
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

realclean: clean
	rm -f Launchers-debug-*.tar.gz* Launchers-release-*.tar.gz*

binaries: snap
