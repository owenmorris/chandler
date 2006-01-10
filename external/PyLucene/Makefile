
VERSION=1.9rc1-6
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PYLUCENE=$(BUILD_ROOT)/PyLucene
SRC=$(PYLUCENE)/PyLucene-src-$(VERSION)

DB_VER=4.4.16
DB_LIB_VER=$(basename $(DB_VER))

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(DEBUG),1)
SUFFIX=d
_SUFFIX=_d
ifeq ($(OS),Cygwin)
PYDBG=-DPy_DEBUG=1
endif
else
SUFFIX=
_SUFFIX=
endif

ifeq ($(OS),Cygwin)
PREFIX_PYTHON=$(PREFIX)/bin
PREFIX_DB=$(BUILD_ROOT)/persistence/db/db-$(DB_VER)
BUILD_DB=build_win32
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene$(_SUFFIX).pyd \
         $(SNAP)/$(SITE)/libiconv-2.dll \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/bin/libdb_java$(subst .,,$(DB_LIB_VER))$(SUFFIX).dll
else

ifeq ($(GCJ_VER),3)
LIBGCJ_VER=5
endif

ifeq ($(GCJ_VER),4)
LIBGCJ_VER=6
endif

ifeq ($(OS),Darwin)
PREFIX_PYTHON=$(PREFIX)/$(FRAMEWORK)
PREFIX_DB=$(PREFIX)/db
BUILD_DB=build_$(SNAP)
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).dylib \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).la \
         $(SNAP)/lib/libgcj.$(LIBGCJ_VER).dylib
ifeq ($(GCJ_VER),3)
MANIFEST:=$(MANIFEST) \
         $(SNAP)/lib/libgcc_s.1.0.dylib \
         $(SNAP)/lib/libstdc++.6.dylib
endif
else

ifeq ($(OS),Linux)
PREFIX_PYTHON=$(PREFIX)
PREFIX_DB=$(PREFIX)/db
BUILD_DB=build_$(SNAP)
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).so \
         $(SNAP)/lib/libgcj.so.$(LIBGCJ_VER)
ifeq ($(GCJ_VER),3)
MANIFEST:=$(MANIFEST) \
         $(SNAP)/lib/libgcc_s.so.1 \
         $(SNAP)/lib/libstdc++.so.6
endif
endif
endif
endif

apply: patches-$(VERSION)
	cd $(SRC); patch -Nup1 < ../patches-$(VERSION); echo ok


ifeq ($(PYLUCENE_CC),)
PYLUCENE_CC=$(GCJ_HOME)/bin/gcc
endif

ifeq ($(PYLUCENE_CXX),)
PYLUCENE_CXX=$(GCJ_HOME)/bin/g++
endif

ifeq ($(PYLUCENE_JCC),)
PYLUCENE_JCC=$(GCJ_HOME)/bin/gcj
endif

ifeq ($(PYLUCENE_JCCH),)
PYLUCENE_JCCH=$(GCJ_HOME)/bin/gcjh
endif

build: expand apply
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_FRAMEWORKS=$(PREFIX)/Library/Frameworks \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            SWIG=$(SWIG) \
            GCJ_HOME=$(GCJ_HOME) \
            GCJ_VER=$(GCJ_VER) \
            PYDBG=$(PYDBG) \
            _SUFFIX=$(_SUFFIX) \
            CC=$(PYLUCENE_CC) \
            CXX=$(PYLUCENE_CXX) \
            JCC=$(PYLUCENE_JCC) \
            JCCH=$(PYLUCENE_JCCH) \
            DB=$(BUILD_ROOT)/persistence/db/db-$(DB_VER) \
            DB_VER=$(DB_VER) \
            DB_LIB_VER=$(DB_LIB_VER) \
            PREFIX_DB=$(PREFIX_DB) \
            BUILD_DB=$(BUILD_DB) \
            PYTHON_VER=$(PYTHON_VER) \
            VERSION=$(VERSION) \
            all install

clean:
	$(MAKE) -C $(SRC) clean

binaries: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz $(MANIFEST); \
	$(MD5) $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz > $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz.md5

install: PyLucene-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf PyLucene-$(SNAP)-$(RELVER).tar.gz

upload: $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz
	scp $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp $(PYLUCENE)/PyLucene-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

PyLucene-src-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/PyLucene-src-$(VERSION).tar.gz

sources: PyLucene-src-$(VERSION).tar.gz

PyLucene-$(VERSION)-expanded: PyLucene-src-$(VERSION).tar.gz
	tar xvzf PyLucene-src-$(VERSION).tar.gz
	touch PyLucene-$(VERSION)-expanded

expand: PyLucene-$(VERSION)-expanded
