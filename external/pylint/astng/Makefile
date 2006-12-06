
VERSION=0.16.3
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
ASTNG=$(BUILD_ROOT)/pylint/astng
SRC=$(ASTNG)/logilab-astng-$(VERSION)
TARBALL=logilab-astng-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build \
        --build-base=$(BUILD) $(DIST_OPT) \
        install --force
	rm -fr $(BUILD_ROOT)/$(SNAP)/$(SITE)/logilab/astng/test

logilab-astng-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/logilab-astng-$(VERSION).tar.gz

sources: logilab-astng-$(VERSION).tar.gz

logilab-astng-$(VERSION)-expanded: logilab-astng-$(VERSION).tar.gz
	tar xvzf logilab-astng-$(VERSION).tar.gz
	touch logilab-astng-$(VERSION)-expanded

expand: logilab-astng-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/logilab/astng -name "*.py[co]" -delete; \
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
