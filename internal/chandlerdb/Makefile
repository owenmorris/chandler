
VERSION=0.7
SUFFIX=$(BRANCH_REV_PREFIX)32
RELVER=$(VERSION)-$(SUFFIX)
CHANDLERDB=$(INTERNAL)/chandlerdb
DB_VER=4.6
SRC=$(CHANDLERDB)
BUILD=build_$(SNAP)
EGG=$(notdir $(shell cd $(BUILD_ROOT); find $(SNAP)/$(SITE) -name 'chandlerdb-$(VERSION)_$(SUFFIX)-py$(PYTHON_VER)-*.egg'))
TARBALL=chandlerdb-$(SNAP)-$(RELVER).tar.gz

include ../Makefile.inc

MANIFEST=$(SNAP)/$(SITE)/chandlerdb

ifeq ($(OS),Cygwin)
_swig=`cygpath -aw $(SWIG)`
_prefix=`cygpath -aw $(PREFIX)`
_chandlerbin=`cygpath -au $(CHANDLERBIN)`
else
_swig=$(SWIG)
_prefix=$(PREFIX)
_chandlerbin=$(CHANDLERBIN)
endif

build:
	PREFIX=$(_prefix) DB_VER=$(DB_VER) VERSION=$(RELVER) \
        $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

ifneq (/,$(CHANDLERDB)/$(BUILD))
clean:
	rm -rf $(BUILD) build
	rm -f $(_chandlerbin)/$(SNAP)/$(TARBALL).inst

endif

realclean: clean

$(TARBALL): $(BUILD_ROOT)/$(SNAP)/$(SITE)/$(EGG)
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/chandlerdb.pth
	tar -C $(BUILD_ROOT) -cvzf $(CHANDLERDB)/$(TARBALL) \
                             $(SNAP)/$(SITE)/$(EGG) \
                             $(SNAP)/$(SITE)/chandlerdb.pth

binaries: $(TARBALL)

snap: $(TARBALL)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)


plop:
	tar -C $(BUILD_ROOT)/$(SNAP) -cf - $(SITE)/$(EGG) | tar -C $(CHANDLERBIN)/$(SNAP) -xvf -

test:
	PREFIX=$(_prefix) DB_VER=$(DB_VER) VERSION=$(RELVER) \
        $(CHANDLERBIN)/$(SNAP)/RunPython setup.py test

test-%:
	PREFIX=$(_prefix) DB_VER=$(DB_VER) VERSION=$(RELVER) \
        $(CHANDLERBIN)/$(SNAP)/RunPython setup.py test --test-suite=tests.Test$*
