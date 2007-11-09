
VERSION=0.8.17
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
PYCHECKER=$(BUILD_ROOT)/pychecker
SRC=$(PYCHECKER)/pychecker-$(VERSION)
TARBALL=pychecker-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(PYTHON_BUILD),)
    BIN=bin
else
    ifeq ($(OS),Darwin)
        BIN=$(FRAMEWORK)/bin
    endif
    ifeq ($(OS),Cygwin)
        BIN=bin/Scripts
    endif
    ifeq ($(OS),Linux)
        BIN=bin
    endif
endif

ifeq ($(OS),Cygwin)
    MANIFEST=$(SNAP)/$(SITE)/pychecker \
             $(SNAP)/$(BIN)/pychecker.bat
else
    MANIFEST=$(SNAP)/$(SITE)/pychecker \
             $(SNAP)/$(BIN)/pychecker
endif

BUILD=build_$(SNAP)


build: expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

pychecker-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/pychecker-$(VERSION).tar.gz

sources: pychecker-$(VERSION).tar.gz

pychecker-$(VERSION)-expanded: pychecker-$(VERSION).tar.gz
	tar xvzf pychecker-$(VERSION).tar.gz
	touch pychecker-$(VERSION)-expanded

expand: pychecker-$(VERSION)-expanded

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(PYCHECKER)/$(TARBALL) \
            --exclude '*.py?' \
        $(MANIFEST)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
