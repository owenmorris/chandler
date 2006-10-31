
VERSION=0.15.0
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)4
COMMON=$(BUILD_ROOT)/pylint/common
SRC=$(COMMON)/common-$(VERSION)
TARBALL=common-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

common-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/common-$(VERSION).tar.gz

sources: common-$(VERSION).tar.gz

common-$(VERSION)-expanded: common-$(VERSION).tar.gz
	tar xvzf common-$(VERSION).tar.gz
	chmod -R u+w common-$(VERSION)
	touch common-$(VERSION)-expanded

expand: common-$(VERSION)-expanded

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
