
SVN_VER=r71371
EGG_VER=3.3.0b2
VERSION=$(EGG_VER)-$(SVN_VER)
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
ZOPE=$(BUILD_ROOT)/zope
SRC=$(ZOPE)/zope.interface-$(VERSION)
BUILD=build_$(SNAP)
TARBALL=zope.interface-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

apply:
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION);echo ok; \
        fi

build: expand apply
	cd $(SRC); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

zope.interface-$(VERSION).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/zope.interface-$(VERSION).tar.bz2

sources: zope.interface-$(VERSION).tar.bz2

zope.interface-$(VERSION)-expanded: zope.interface-$(VERSION).tar.bz2
	tar -xvjf zope.interface-$(VERSION).tar.bz2
	touch $@

expand: zope.interface-$(VERSION)-expanded

binaries: strip
	# this ln statement will fail if there is more than one match for the
	# zope.interface egg name pattern
	ln -sf $(BUILD_ROOT)/$(SNAP)/$(SITE)/$(notdir $(wildcard $(BUILD_ROOT)/$(SNAP)/$(SITE)/zope.interface-$(EGG_VER)-py$(PYTHON_VER)-*.egg))/zope $(BUILD_ROOT)/$(SNAP)/$(SITE)/zope
	tar -C $(BUILD_ROOT) -cvzf $(ZOPE)/$(TARBALL) \
                             --exclude tests \
                             --exclude testing \
                             --exclude '*.py[co]' \
                                   $(SNAP)/$(SITE)/zope/__init__.py \
                                   $(SNAP)/$(SITE)/zope/interface

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
