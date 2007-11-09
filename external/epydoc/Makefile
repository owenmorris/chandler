
VERSION=3.0beta1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
EPYDOC=$(BUILD_ROOT)/epydoc
SRC=$(EPYDOC)/epydoc-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=epydoc-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

.PHONY: patches-$(VERSION)

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION); echo ok; \
        fi

build: expand apply
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

epydoc-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/epydoc-$(VERSION).tar.gz

sources: epydoc-$(VERSION).tar.gz

epydoc-$(VERSION)-expanded: epydoc-$(VERSION).tar.gz
	tar xvzf epydoc-$(VERSION).tar.gz
	touch epydoc-$(VERSION)-expanded

expand: epydoc-$(VERSION)-expanded

binaries: strip
	tar -C $(BUILD_ROOT) -cvzf $(EPYDOC)/$(TARBALL) \
        --exclude test --exclude '*.py?' \
        $(SNAP)/$(SITE)/epydoc

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
