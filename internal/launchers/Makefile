
include ../Makefile.inc

RELVER=0.1-1
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

build:
        cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
        cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)

endif

ifeq ($(OS),Cygwin)

ARCHIVE: $(LAUNCHERS)/win/

build:
	cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
	cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
	cd $(LAUNCHERS)/win; \
	. $(BUILD_ROOT)/cygenv.sh; \
	make
endif

ifeq ($(OS),Linux)

ARCHIVE: $(LAUNCHERS)/linux/

build:
        cp $(LAUNCHERS)/scripts/RunChandler.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunChandler$(SCRIPT_EXTENTION)
        cp $(LAUNCHERS)/scripts/RunPython.$(SNAP).$(PLATFORM) $(BUILD_ROOT)/$(SNAP)/RunPython$(SCRIPT_EXTENTION)
        cd $(LAUNCHERS)/linux; \
        make

endif

#  common to all platforms

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERS)/LAUNCHERS-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/LAUNCHERS*

clean:
	rm -rf $(BUILD)

upload: LAUNCHERS-$(SNAP)-$(RELVER).tar.gz
	scp LAUNCHERS-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
