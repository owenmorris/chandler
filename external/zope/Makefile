
SVN_VER=r71371
EGG_VER=3.3.0b2
VERSION=$(EGG_VER)-$(SVN_VER)
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)4
ZOPE=$(BUILD_ROOT)/zope
SRC=$(ZOPE)/zope.interface-$(VERSION)
BUILD=build_$(SNAP)
EGG=$(notdir $(shell cd $(BUILD_ROOT); find $(SNAP)/$(SITE) -name 'zope.interface-$(EGG_VER)-py$(PYTHON_VER)-*.egg'))
TARBALL=zope.interface-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

apply:
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION);echo ok; \
        fi

build: expand apply
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force

zope.interface-$(VERSION).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/zope.interface-$(VERSION).tar.bz2

sources: zope.interface-$(VERSION).tar.bz2

zope.interface-$(VERSION)-expanded: zope.interface-$(VERSION).tar.bz2
	tar -xvjf zope.interface-$(VERSION).tar.bz2
	touch $@

expand: zope.interface-$(VERSION)-expanded

binaries: strip
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/zope.interface.pth
	tar -C $(BUILD_ROOT) -cvzf $(ZOPE)/$(TARBALL) \
                             $(SNAP)/$(SITE)/$(EGG) \
                             $(SNAP)/$(SITE)/zope.interface.pth

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
