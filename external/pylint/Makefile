
VERSION=0.13.1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
PYLINT=$(BUILD_ROOT)/pylint
SRC=$(PYLINT)/pylint-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=pylint-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

build-common:
	$(MAKE) -C common DEBUG=$(DEBUG) all

build-astng:
	$(MAKE) -C astng DEBUG=$(DEBUG) all

build: build-common build-astng expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

pylint-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/pylint-$(VERSION).tar.gz

sources-common:
	$(MAKE) -C common DEBUG=$(DEBUG) sources

sources-astng:
	$(MAKE) -C astng DEBUG=$(DEBUG) sources

sources: sources-common sources-astng pylint-$(VERSION).tar.gz

pylint-$(VERSION)-expanded: pylint-$(VERSION).tar.gz
	tar xvzf pylint-$(VERSION).tar.gz
	chmod -R u+w pylint-$(VERSION)
	touch pylint-$(VERSION)-expanded

expand-common:
	$(MAKE) -C common DEBUG=$(DEBUG) expand

expand-astng:
	$(MAKE) -C astng DEBUG=$(DEBUG) expand

expand: expand-common expand-astng pylint-$(VERSION)-expanded

binaries-common:
	$(MAKE) -C common DEBUG=$(DEBUG) binaries

binaries-astng:
	$(MAKE) -C astng DEBUG=$(DEBUG) binaries

binaries: binaries-common binaries-astng  strip
	tar -C $(BUILD_ROOT) -cvzf $(PYLINT)/pylint-$(SNAP)-$(RELVER).tar.gz \
        --exclude test --exclude '*.py?' \
        $(SNAP)/$(SITE)/pylint

install-common:
	$(MAKE) -C common DEBUG=$(DEBUG) install

install-astng:
	$(MAKE) -C astng DEBUG=$(DEBUG) install

install: install-common install-astng $(TARBALL)
	cp $(TARBALL) $(CHANDLERARCHIVES)

clean-common:
	$(MAKE) -C common DEBUG=$(DEBUG) clean

clean-astng:
	$(MAKE) -C astng DEBUG=$(DEBUG) clean

ifneq (/,$(SRC)/$(BUILD))
clean: clean-common clean-astng
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

upload-common:
	$(MAKE) -C common DEBUG=$(DEBUG) upload

upload-astng:
	$(MAKE) -C astng DEBUG=$(DEBUG) upload

upload: upload-common upload-astng $(TARBALL)
	scp $(TARBALL) $(UPLOAD)

_realclean::
	rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded
	rm -rf $(SRC)*
	$(MAKE) -C common DEBUG=$(DEBUG) _realclean
	$(MAKE) -C astng DEBUG=$(DEBUG) _realclean
