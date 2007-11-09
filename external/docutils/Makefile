
VERSION=0.4
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
DOCUTILS=$(BUILD_ROOT)/docutils
SRC=$(DOCUTILS)/docutils-$(VERSION)
TARBALL=docutils-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

ifeq ($(PYTHON_BUILD),)
    SCRIPTS=$(SNAP)/bin
else
    ifeq ($(OS),Darwin)
        SCRIPTS=$(SNAP)/$(FRAMEWORK)/bin
    endif
    ifeq ($(OS),Cygwin)
        SCRIPTS=$(SNAP)/bin/Scripts
    endif
    ifeq ($(OS),Linux)
        SCRIPTS=$(SNAP)/bin
    endif
endif

build: expand
	cd $(SRC); $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                                      install --force	

sources: docutils-$(VERSION).tar.gz

docutils-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/docutils-$(VERSION).tar.gz

expand: docutils-$(VERSION)-expanded

docutils-$(VERSION)-expanded: sources
	tar -xvzf docutils-$(VERSION).tar.gz
	touch $@

binaries:
	tar -C $(BUILD_ROOT) -cvzf $(DOCUTILS)/$(TARBALL) \
                             --exclude '*.py?' \
                             $(SNAP)/$(SITE)/docutils \
                             $(SNAP)/$(SITE)/roman.py \
                             $(SCRIPTS)/rst2html.py \
                             $(SCRIPTS)/rst2latex.py \
                             $(SCRIPTS)/rst2newlatex.py \
                             $(SCRIPTS)/rst2pseudoxml.py \
                             $(SCRIPTS)/rst2s5.py \
                             $(SCRIPTS)/rst2xml.py

install:
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

ifneq (/,$(SRC))
clean:
	rm -rf $(SRC)
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif
