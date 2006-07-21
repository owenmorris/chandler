VERSION=0.6b3

SETUPTOOLS=$(BUILD_ROOT)/setuptools
BUILD=build_$(SNAP)
TARBALL=setuptools-$(VERSION)-py2.4.egg

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)

build: $(TARBALL)
	cd $(SETUPTOOLS); \
    PYTHONPATH=$(TARBALL) \
    $(PYTHON) ez_setup.py $(TARBALL)
else

ifeq ($(OS),Darwin)

build: $(TARBALL)
	cd $(SETUPTOOLS); \
    MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
    PYTHONPATH=$(TARBALL) \
    $(PYTHON) ez_setup.py $(TARBALL)

else

build: $(TARBALL)
	cd $(SETUPTOOLS); \
    PYTHONPATH=$(TARBALL) \
    $(PYTHON) ez_setup.py $(TARBALL)

endif
endif

$(TARBALL):
	$(CURL) http://builds.osafoundation.org/external/$(TARBALL)

sources: $(TARBALL)

expand:

binaries: 

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

clean:
	rm -f $(TARBALL)

_realclean::
	@rm -f $(TARBALL)

