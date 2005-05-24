
include ../Makefile.inc

RELVER=0.5-1
LAUNCHERS=$(INTERNAL)/launchers

BUILD=build_$(SNAP)


ifeq ($(PLATFORM),windows)
    SCRIPT_EXTENTION=".bat"
else
    SCRIPT_EXTENTION=
endif

ifeq ($(OS),Darwin)

LAUNCHER_FILES=
LIB_FILES=

# Nothing to be done for clean
clean:


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

build: apply
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
	make -C $(LAUNCHERS)/win

apply:
ifeq ($(PYTHON_VER),2.4)
	patch -Nup0 < patches-2.4; echo ok
endif

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

# Nothing to be done for clean
clean:

build:
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/linux/$(LAUNCHER) $(BUILD_ROOT)/$(LAUNCHER)

endif

#  common to all platforms

MANIFEST=$(SNAP)/Run* \
         $(LAUNCHER_FILES) \
         $(LIB_FILES)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERS)/Launchers-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) Launchers-$(SNAP)-$(RELVER).tar.gz > Launchers-$(SNAP)-$(RELVER).tar.gz.md5

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

realclean: clean
	rm -f Launchers-debug-*.tar.gz* Launchers-release-*.tar.gz*

upload: Launchers-$(SNAP)-$(RELVER).tar.gz
	scp Launchers-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp Launchers-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)
