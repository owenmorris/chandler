
VERSION=0.16.1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
GETTEXT=$(BUILD_ROOT)/gettext
SRC=$(GETTEXT)/gettext-$(VERSION)
TARBALL=gettext-$(SNAP)-$(RELVER).tar.gz
BUILD=build_$(SNAP)

include ../Makefile.inc

$(SRC)/Makefile:
	cd $(SRC); ./configure --prefix=$(SRC)/$(SNAP)

build: expand $(SRC)/Makefile
	$(MAKE) -C $(SRC)
	$(MAKE) -C $(SRC) install
	tar -C $(SRC) -cf - $(SNAP) | tar -C $(PREFIX) -xvf -

ifneq (/,$(SRC)/$(SNAP))
clean:
	rm -rf $(SRC)/$(SNAP)
endif

$(TARBALL):
	tar -C $(SRC) -cvzf $@ $(SNAP)

binaries: $(TARBALL)

gettext-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/gettext-$(VERSION).tar.gz 

sources: gettext-$(VERSION).tar.gz

gettext-$(VERSION)-expanded: gettext-$(VERSION).tar.gz
	tar -xvzf gettext-$(VERSION).tar.gz
	touch $@

expand: gettext-$(VERSION)-expanded
