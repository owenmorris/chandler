
RELVER=0.7-$(BRANCH_REV_PREFIX)26
CHANDLERDB=$(INTERNAL)/chandlerdb
DB_VER=4.5
SRC=$(CHANDLERDB)
BUILD=build_$(SNAP)
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
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
        PREFIX=$(_prefix) \
        DB_VER=$(DB_VER) \
        VERSION=$(RELVER) \
        $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

ifneq (/,$(CHANDLERDB)/$(BUILD))
clean:
	rm -rf $(BUILD)
	rm -f $(_chandlerbin)/$(SNAP)/$(TARBALL).inst

endif

realclean: clean

$(TARBALL): strip
	cd $(BUILD_ROOT); \
	find $(MANIFEST) -name "*.py[co]" -delete; \
        tar -cvzf $(CHANDLERDB)/$(TARBALL) $(MANIFEST)

binaries: $(TARBALL)

snap: $(TARBALL)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)


plop:
	tar -C $(BUILD_ROOT) -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -
