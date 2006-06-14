
VERSION=1.2.6-20050316
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3
ETREE=$(BUILD_ROOT)/elementtree
SRC=$(ETREE)/elementtree-$(VERSION)
TARBALL=elementtree-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: expand
	cd $(SRC); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

elementtree-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/elementtree-$(VERSION).tar.gz

sources: elementtree-$(VERSION).tar.gz

elementtree-$(VERSION)-expanded: elementtree-$(VERSION).tar.gz
	tar xvzf elementtree-$(VERSION).tar.gz
	chmod -R u+w elementtree-$(VERSION)
	touch elementtree-$(VERSION)-expanded

expand: elementtree-$(VERSION)-expanded

binaries: strip
	cd $(BUILD_ROOT); \
    find $(SNAP)/$(SITE)/elementtree -name "*.pyc" | xargs rm -f; \
    find $(SNAP)/$(SITE)/elementtree -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(ETREE)/$(TARBALL) \
                  --exclude test \
                  $(SNAP)/$(SITE)/elementtree

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

_realclean::
	rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded
	rm -rf $(SRC)*
