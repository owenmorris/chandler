
VERSION=0.16.0
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)3
ASTNG=$(BUILD_ROOT)/pylint/astng
SRC=$(ASTNG)/astng-$(VERSION)
TARBALL=astng-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build \
        --build-base=$(BUILD) $(DIST_OPT) \
        install --force
	rm -fr $(BUILD_ROOT)/$(SNAP)/$(SITE)/logilab/astng/test

astng-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/astng-$(VERSION).tar.gz

sources: astng-$(VERSION).tar.gz

astng-$(VERSION)-expanded: astng-$(VERSION).tar.gz
	tar xvzf astng-$(VERSION).tar.gz
	touch astng-$(VERSION)-expanded

expand: astng-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/logilab/astng -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/logilab/astng -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(ASTNG)/$(TARBALL) \
                  $(SNAP)/$(SITE)/logilab/astng

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
