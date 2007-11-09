
VERSION=0.6-$(SVNVER)
SVNVER=81
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PYICU=$(BUILD_ROOT)/PyICU
SRC=$(PYICU)/PyICU-$(VERSION)
BUILD=$(SNAP)
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
MANIFEST=$(SNAP)/$(SITE)/PyICU.py $(SNAP)/$(SITE)/_PyICU$(_SUFFIX).pyd

build: expand
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            PREFIX_ICU=$(PREFIX) \
            ICU_INC=`cygpath -am $(PREFIX)/include/icu` \
            PYTHON_VER=$(PYTHON_VER) \
            VERSION=$(VERSION) \
            all install
else

ifeq ($(OS),Darwin)
ifeq ($(PYTHON_BUILD),)
    PREFIX_PYTHON=$(FRAMEWORK)
    PREFIX_FRAMEWORKS=/System/Library/Frameworks
    PYTHON_SITE=$(BUILD_ROOT)/$(SNAP)/$(SITE)
else
    PREFIX_PYTHON=$(PREFIX)/$(FRAMEWORK)
    PREFIX_FRAMEWORKS=$(PREFIX)/Library/Frameworks
    PYTHON_SITE=$(PREFIX_PYTHON)/lib/python$(PYTHON_VER)/site-packages
endif

MANIFEST=$(SNAP)/$(SITE)/PyICU.py $(SNAP)/$(SITE)/_PyICU.so

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

build: expand apply
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) \
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_FRAMEWORKS=$(PREFIX_FRAMEWORKS) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            PREFIX_ICU=$(PREFIX)/icu \
            PYTHON_VER=$(PYTHON_VER) \
            PYTHON_SITE=$(PYTHON_SITE) \
            VERSION=$(VERSION) \
            all install
else

ifeq ($(OS),Linux)
MANIFEST=$(SNAP)/$(SITE)/PyICU.py $(SNAP)/$(SITE)/_PyICU.so

ifeq ($(ICU_BUILD),)
    PREFIX_ICU=/usr
else
    PREFIX_ICU=$(PREFIX)/icu
endif

ifeq ($(PYTHON_BUILD),)
    PREFIX_PYTHON=/usr
    PYTHON_SITE=$(BUILD_ROOT)/$(SNAP)/$(SITE)
else
    PREFIX_PYTHON=$(PREFIX)
    PYTHON_SITE=$(BUILD_ROOT)/$(SNAP)/$(SITE)
endif

build: expand
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            PREFIX_ICU=$(PREFIX_ICU) \
            PYTHON_VER=$(PYTHON_VER) \
            PYTHON_SITE=$(PYTHON_SITE) \
            VERSION=$(VERSION) \
            all install

endif
endif
endif

ifneq (/,$(SRC))
clean:
	$(MAKE) -C $(SRC) clean
endif

binaries: strip
	cd $(BUILD_ROOT); \
    tar -cvzf $(PYICU)/$(TARBALL) $(MANIFEST)

sources: PyICU-$(VERSION)-expanded

PyICU-$(VERSION)-expanded:
	svn export -r $(SVNVER) http://svn.osafoundation.org/pyicu/trunk PyICU-$(VERSION)
	touch PyICU-$(VERSION)-expanded

expand: PyICU-$(VERSION)-expanded

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

test:
	$(MAKE) -C $(SRC) PYTHON=$(PYTHON) test

