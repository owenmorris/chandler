VERSION=8.2.0
SRC=$(BUILD_ROOT)/twisted/Twisted-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

dist_dir = $(CHANDLERARCHIVES)

ifeq ($(OS),Cygwin)
    dist_dir := $(shell cygpath -aw $(dist_dir))
    PATCH = .Twisted-$(VERSION).patch-applied
else
    PATCH =
endif

ifneq ($(PATCH),)
    SETUP_EXTRA = egg_info -b -r26634
else
    SETUP_EXTRA =
endif

Twisted-$(VERSION).tar.bz2:
	$(CURL) http://builds.osafoundation.org/external/$@

build: expand

binaries: expand
	(cd $(SRC)/twisted && \
	$(PYTHON) setup.py $(SETUP_EXTRA) bdist_egg --dist-dir='$(dist_dir)')

install: expand
	(cd $(SRC)/twisted && \
	$(PYTHON) setup.py $(SETUP_EXTRA) install --install-lib='$(INSTALL_DIR)')

expand: $(PATCH) Twisted-$(VERSION)

.Twisted-$(VERSION).patch-applied: Twisted-$(VERSION)
	(cat patch-8.2.0-r26634 | (cd '$<'/twisted && patch -p0)) && \
	touch $@

Twisted-$(VERSION): Twisted-$(VERSION).tar.bz2
	$(PYTHON) -m easy_install -eb $@ --find-links . Twisted==$(VERSION)

sources: Twisted-$(VERSION).tar.bz2

clean:
	rm -rf Twisted-$(VERSION) $(PATCH)
	rm -rf '$(INSTALL_DIR)'/Twisted-$(VERSION)*.egg

test:
	$(PYTHON) '$(INSTALL_DIR)'/trial twisted
