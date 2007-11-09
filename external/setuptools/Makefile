
VERSION=0.6c6
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
SETUPTOOLS=$(BUILD_ROOT)/setuptools
BUILD=build_$(SNAP)
EGG=setuptools-$(subst -,_,$(VERSION))-py$(PYTHON_VER).egg
TARBALL=setuptools-$(SNAP)-$(RELVER).tar.gz
SRC=$(SETUPTOOLS)/setuptools-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

MANIFEST=$(SNAP)/$(SITE)/$(EGG) \
         $(SNAP)/$(SITE)/setuptools.pth

ifeq ($(PYTHON_BUILD),)
    MANIFEST:=$(MANIFEST) $(SNAP)/$(SITE)/site.py
endif


build: expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

setuptools-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/$@

sources: setuptools-$(VERSION).tar.gz

setuptools-$(VERSION)-expanded: setuptools-$(VERSION).tar.gz
	tar -xvzf setuptools-$(VERSION).tar.gz
	touch setuptools-$(VERSION)-expanded

expand: setuptools-$(VERSION)-expanded

binaries: $(BUILD_ROOT)/$(SNAP)/$(SITE)/$(EGG)
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/setuptools.pth
	tar -C $(BUILD_ROOT) -cvzf $(SETUPTOOLS)/$(TARBALL) $(MANIFEST)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)


ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
