
include ../Makefile.inc

RELVER=0.5-28
CHANDLERDB=$(INTERNAL)/chandlerdb

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
        $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

clean:
	rm -rf $(BUILD)

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
