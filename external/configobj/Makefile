
VERSION=4.3.2
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
CONFIGOBJ=$(BUILD_ROOT)/configobj
SRC=$(CONFIGOBJ)/configobj-$(VERSION)
TARBALL=configobj-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build: expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force	

sources: configobj-$(VERSION).tar.bz2

configobj-$(VERSION).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/configobj-$(VERSION).tar.bz2

expand: configobj-$(VERSION)-expanded

configobj-$(VERSION)-expanded: sources
	tar -xvjf configobj-$(VERSION).tar.bz2
	touch $@

binaries:
	tar -C $(BUILD_ROOT) -cvzf $(CONFIGOBJ)/$(TARBALL) \
                             $(SNAP)/$(SITE)/configobj.py \
                             $(SNAP)/$(SITE)/validate.py 

install:
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC))
clean:
	rm -rf $(SRC)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
