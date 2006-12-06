
VERSION=0.6c4dev-r52887

SETUPTOOLS=$(BUILD_ROOT)/setuptools
BUILD=build_$(SNAP)
TARBALL=setuptools-$(subst -,_,$(VERSION))-py$(PYTHON_VER).egg
SRC=$(SETUPTOOLS)/setuptools-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
            $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                               install --force
	cp -p $(BUILD_ROOT)/$(SNAP)/$(SITE)/$(TARBALL) .

setuptools-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/$@

sources: setuptools-$(VERSION).tar.gz

setuptools-$(VERSION)-expanded: setuptools-$(VERSION).tar.gz
	tar xvzf setuptools-$(VERSION).tar.gz
	touch setuptools-$(VERSION)-expanded

expand: setuptools-$(VERSION)-expanded

binaries:

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

drop:
	# chandler/Makefile expects it there
	cp -p $(TARBALL) $(CHANDLERARCHIVES)
