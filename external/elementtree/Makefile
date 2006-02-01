
VERSION=1.2.6-20050316
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
ETREE=$(BUILD_ROOT)/elementtree
SRC=$(ETREE)/elementtree-$(VERSION)

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

binaries:
	cd $(BUILD_ROOT); \
    find $(SNAP)/$(SITE)/elementtree -name "*.pyc" | xargs rm -f; \
    find $(SNAP)/$(SITE)/elementtree -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(ETREE)/elementtree-$(SNAP)-$(RELVER).tar.gz \
                  --exclude test \
                  $(SNAP)/$(SITE)/elementtree

install: elementtree-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf elementtree-$(SNAP)-$(RELVER).tar.gz

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif

upload: elementtree-$(SNAP)-$(RELVER).tar.gz
	scp elementtree-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

_realclean::
	rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded
	rm -rf $(SRC)*
