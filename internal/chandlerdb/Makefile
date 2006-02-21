
include ../Makefile.inc

RELVER=0.6-$(BRANCH_REV_PREFIX)15
CHANDLERDB=$(INTERNAL)/chandlerdb
DB_VER=4.4

BUILD=build_$(SNAP)

MANIFEST=$(SNAP)/$(SITE)/chandlerdb

ifeq ($(OS),Cygwin)
_swig=`cygpath -aw $(SWIG)`
_prefix=`cygpath -aw $(PREFIX)`
else
_swig=$(SWIG)
_prefix=$(PREFIX)
endif


build:
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
        PREFIX=$(_prefix) \
	DB_VER=$(DB_VER) \
        $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

ifneq (/,$(CHANDLERDB)/$(BUILD))
clean:
	rm -rf $(BUILD)
endif

realclean: clean

upload: chandlerdb-$(SNAP)-$(RELVER).tar.gz
	scp chandlerdb-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

snap: 
	cd $(BUILD_ROOT); \
	find $(MANIFEST) -name "*.pyc" | xargs rm -f; \
	find $(MANIFEST) -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(CHANDLERDB)/chandlerdb-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

install:
	tar -C $(BUILD_ROOT) -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -
