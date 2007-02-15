
VERSION=0.6c6dev-r53674
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
SETUPTOOLS=$(BUILD_ROOT)/setuptools
BUILD=build_$(SNAP)
EGG=setuptools-$(subst -,_,$(VERSION))-py$(PYTHON_VER).egg
TARBALL=setuptools-$(SNAP)-$(RELVER).tar.gz
SRC=$(SETUPTOOLS)/setuptools-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
            $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                               install --force

setuptools-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/$@

sources: setuptools-$(VERSION).tar.gz

setuptools-$(VERSION)-expanded: setuptools-$(VERSION).tar.gz
	tar -xvzf setuptools-$(VERSION).tar.gz
	touch setuptools-$(VERSION)-expanded

expand: setuptools-$(VERSION)-expanded

ifeq ($(OS),Cygwin)
binaries: $(BUILD_ROOT)/$(SNAP)/$(SITE)/$(EGG)
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/setuptools.pth
	tar -C $(BUILD_ROOT) -cvzf $(SETUPTOOLS)/$(TARBALL) \
             $(SNAP)/$(SITE)/$(EGG) \
             $(SNAP)/$(SITE)/setuptools.pth \
             $(SNAP)/$(PYTHON_BINDIR)/Scripts/easy_install.exe \
             $(SNAP)/$(PYTHON_BINDIR)/Scripts/easy_install-$(PYTHON_VER).exe
else
binaries: $(BUILD_ROOT)/$(SNAP)/$(SITE)/$(EGG)
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/setuptools.pth
	tar -C $(BUILD_ROOT) -cvzf $(SETUPTOOLS)/$(TARBALL) \
             $(SNAP)/$(SITE)/$(EGG) \
             $(SNAP)/$(SITE)/setuptools.pth \
             $(SNAP)/$(PYTHON_BINDIR)/easy_install \
             $(SNAP)/$(PYTHON_BINDIR)/easy_install-$(PYTHON_VER)
endif

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)


ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
