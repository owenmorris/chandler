
VERSION=0.21.2
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
COMMON=$(BUILD_ROOT)/pylint/common
SRC=$(COMMON)/logilab-common-$(VERSION)
TARBALL=logilab-common-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build: expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

logilab-common-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/logilab-common-$(VERSION).tar.gz

sources: logilab-common-$(VERSION).tar.gz

logilab-common-$(VERSION)-expanded: logilab-common-$(VERSION).tar.gz
	tar xvzf logilab-common-$(VERSION).tar.gz
	chmod -R u+w logilab-common-$(VERSION)
	touch logilab-common-$(VERSION)-expanded

expand: logilab-common-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/logilab -name "*.py[co]" -delete; \
        tar -cvzf $(COMMON)/$(TARBALL) \
                  --exclude test $(SNAP)/$(SITE)/logilab/common \
                  $(SNAP)/$(SITE)/logilab/__init__.py


install: $(TARBALL)
	cp $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

_realclean::
	rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded
	rm -rf $(SRC)*

upload: $(TARBALL)
	scp $(TARBALL) $(UPLOAD)
