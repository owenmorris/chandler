
VERSION=1.1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)6
DATEUTIL=$(BUILD_ROOT)/dateutil
SRC=python-dateutil-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=dateutil-$(SNAP)-$(RELVER).tar.gz
MANIFEST=$(SNAP)/$(SITE)/dateutil

include ../Makefile.inc

$(SRC).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/$(SRC).tar.bz2

sources: python-dateutil-$(VERSION).tar.bz2

$(SRC)-expanded: $(SRC).tar.bz2
	tar xvjf $(SRC).tar.bz2
	touch $(SRC)-expanded

expand: $(SRC)-expanded

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

build: expand apply
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(DATEUTIL)/$(TARBALL) \
        --exclude '*.py?' \
        $(MANIFEST)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test:
	cd $(SRC); \
    $(PYTHON) test.py -v


ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
