
VERSION=0.8.6
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PDT=$(BUILD_ROOT)/parsedatetime
SRC=$(PDT)/parsedatetime-$(VERSION)
TARBALL=parsedatetime-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

ifeq ($(OS),Cygwin)
build: expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install_lib --force --install-dir=`cygpath -aw $(BUILD_ROOT)/$(SNAP)/$(SITE)`
else
build: expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install_lib --force --install-dir=$(BUILD_ROOT)/$(SNAP)/$(SITE)
endif

parsedatetime-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/parsedatetime-$(VERSION).tar.gz

sources: parsedatetime-$(VERSION).tar.gz

parsedatetime-$(VERSION)-expanded: parsedatetime-$(VERSION).tar.gz
	tar xvzf parsedatetime-$(VERSION).tar.gz
	touch parsedatetime-$(VERSION)-expanded

expand: parsedatetime-$(VERSION)-expanded

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(PDT)/$(TARBALL) \
        --exclude '*.py?' \
        $(SNAP)/$(SITE)/parsedatetime

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test:
	cd $(SRC); \
    $(PYTHON) run_tests.py parsedatetime

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
