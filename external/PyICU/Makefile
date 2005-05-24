
VERSION=0.1
RELVER=$(VERSION)-1
PYICU=$(BUILD_ROOT)/PyICU
SRC=$(PYICU)/PyICU-$(VERSION)

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

clean:
	$(MAKE) -C $(SRC) clean

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYICU)/pyicu-$(SNAP)-$(RELVER).tar.gz $(MANIFEST); \
	$(MD5) $(PYICU)/pyicu-$(SNAP)-$(RELVER).tar.gz > $(PYICU)/pyicu-$(SNAP)-$(RELVER).tar.gz.md5

install: pyicu-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf pyicu-$(SNAP)-$(RELVER).tar.gz

upload: $(PYICU)/pyicu-$(SNAP)-$(RELVER).tar.gz
	scp $(PYICU)/pyicu-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp $(PYICU)/pyicu-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

PyICU-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/PyICU-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/PyICU-$(VERSION).tar.gz.md5

sources: PyICU-$(VERSION).tar.gz

PyICU-$(VERSION)-expanded: PyICU-$(VERSION).tar.gz
	tar xvzf PyICU-$(VERSION).tar.gz
	touch PyICU-$(VERSION)-expanded

expand: PyICU-$(VERSION)-expanded
