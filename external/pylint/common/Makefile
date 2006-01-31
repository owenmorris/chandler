
VERSION=0.12.0
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
COMMON=$(BUILD_ROOT)/pylint/common
SRC=$(COMMON)/common-$(VERSION)

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
	find $(SNAP)/$(SITE)/logilab -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/logilab -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(COMMON)/common-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/logilab \
                  --exclude test

install: common-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf common-$(SNAP)-$(RELVER).tar.gz

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif

_realclean::
	rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded
	rm -rf $(SRC)*

upload: common-$(SNAP)-$(RELVER).tar.gz
	scp common-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
