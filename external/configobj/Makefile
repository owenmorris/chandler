
VERSION=4.3.2
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
CONFIGOBJ=$(BUILD_ROOT)/configobj
SRC=$(CONFIGOBJ)/$(TARBALL)
TARBALL=configobj-$(VERSION)-py$(PYTHON_VER).egg

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

ifeq ($(OS),Darwin)
    EASYINSTALL=$(PREFIX)/$(FRAMEWORK)/bin/easy_install
else
    EASYINSTALL=$(PREFIX)/bin/easy_install
endif

build: sources
	$(EASYINSTALL) $(TARBALL)

$(TARBALL):
	$(CURL) http://builds.osafoundation.org/external/$(TARBALL)

sources: $(TARBALL)

expand: sources

binaries: sources

install: sources
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC))
clean:
	rm -rf $(SRC)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
