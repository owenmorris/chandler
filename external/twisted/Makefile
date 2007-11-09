
VERSION=r18795
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
TWISTED=$(BUILD_ROOT)/twisted
SRC=$(TWISTED)/twisted-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=twisted-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

.PHONY: patches-$(VERSION)

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION);echo ok; \
        fi

build: expand apply
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

twisted-$(VERSION).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/twisted-$(VERSION).tar.bz2

sources: twisted-$(VERSION).tar.bz2

twisted-$(VERSION)-expanded: twisted-$(VERSION).tar.bz2
	tar xvjf twisted-$(VERSION).tar.bz2
	touch twisted-$(VERSION)-expanded

expand: twisted-$(VERSION)-expanded

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(TWISTED)/$(TARBALL) \
          --exclude test --exclude '*.py?' \
          $(SNAP)/$(SITE)/twisted

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test:
	cd $(SRC); $(PYTHON) setup.py test

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
