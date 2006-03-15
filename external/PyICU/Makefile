
VERSION=0.4-$(SVNVER)
SVNVER=53
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PYICU=$(BUILD_ROOT)/PyICU
SRC=$(PYICU)/PyICU-$(VERSION)
TARBALL=PyICU-$(SNAP)-$(RELVER).tar.gz

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)
ifeq ($(DEBUG),1)
SUFFIX=d
_SUFFIX=_d
else
SUFFIX=
_SUFFIX=
endif
PREFIX_PYTHON=$(PREFIX)/bin
MANIFEST=$(SNAP)/$(SITE)/PyICU.py $(SNAP)/$(SITE)/_PyICU$(_SUFFIX).pyd \
         $(SNAP)/$(SITE)/PyICU_*.py $(SNAP)/$(SITE)/_PyICU_*$(_SUFFIX).pyd \
         $(SNAP)/$(SITE)/libPyICU$(SUFFIX).dll

build: expand
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            PREFIX_ICU=$(PREFIX) \
            ICU_INC=`cygpath -am $(PREFIX)/include/icu` \
            SWIG=$(SWIG) \
            PYTHON_VER=$(PYTHON_VER) \
            VERSION=$(VERSION) \
            all install
else

ifeq ($(OS),Darwin)
PREFIX_PYTHON=$(PREFIX)/$(FRAMEWORK)

MANIFEST=$(SNAP)/$(SITE)/PyICU.py $(SNAP)/$(SITE)/_PyICU.so \
         $(SNAP)/$(SITE)/PyICU_*.py $(SNAP)/$(SITE)/_PyICU_*.so \
         $(SNAP)/lib/libPyICU$(SUFFIX).dylib

build: expand
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_FRAMEWORKS=$(PREFIX)/Library/Frameworks \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            PREFIX_ICU=$(PREFIX)/icu \
            SWIG=$(SWIG) \
            PYTHON_VER=$(PYTHON_VER) \
            VERSION=$(VERSION) \
            all install
else

ifeq ($(OS),Linux)
PREFIX_PYTHON=$(PREFIX)
MANIFEST=$(SNAP)/$(SITE)/PyICU.py $(SNAP)/$(SITE)/_PyICU.so \
         $(SNAP)/$(SITE)/PyICU_*.py $(SNAP)/$(SITE)/_PyICU_*.so \
         $(SNAP)/lib/libPyICU$(SUFFIX).so

build: expand
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            PREFIX_ICU=$(PREFIX)/icu \
            SWIG=$(SWIG) \
            PYTHON_VER=$(PYTHON_VER) \
            VERSION=$(VERSION) \
            all install

endif
endif
endif

clean: PyICU-$(VERSION)-expanded
	$(MAKE) -C $(SRC) clean

binaries: 
	cd $(BUILD_ROOT); \
    tar -cvzf $(PYICU)/$(TARBALL) $(MANIFEST)

install: $(TARBALL)
	cp $(TARBALL) $(CHANDLERARCHIVES)

upload: $(PYICU)/$(TARBALL)
	scp $(PYICU)/$(TARBALL) $(UPLOAD)

sources: PyICU-$(VERSION)-expanded

PyICU-$(VERSION)-expanded:
	svn export -r $(SVNVER) http://svn.osafoundation.org/pyicu/trunk PyICU-$(VERSION)
	touch PyICU-$(VERSION)-expanded

expand: PyICU-$(VERSION)-expanded
