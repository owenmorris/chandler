
VERSION=2.0.0-4
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PYLUCENE=$(BUILD_ROOT)/PyLucene
SRC=$(PYLUCENE)/PyLucene-src-$(VERSION)
BUILD=$(SNAP)
TARBALL=PyLucene-$(SNAP)-$(RELVER).tar.gz

DB_VER=4.4.20
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
PREFIX_DB=$(BUILD_ROOT)/db/db-$(DB_VER)
BUILD_DB=build_win32
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene$(_SUFFIX).pyd \
         $(SNAP)/$(SITE)/libiconv-2.dll \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/bin/libdb_java$(subst .,,$(DB_LIB_VER))$(SUFFIX).dll
LIB_INSTALL=
GCJ_STATIC=1
else

ifeq ($(OS),Darwin)
PREFIX_PYTHON=$(PREFIX)/$(FRAMEWORK)
PREFIX_DB=$(PREFIX)/db
BUILD_DB=build_$(SNAP)
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).dylib \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).la
ifeq ($(GCJ_VER),3)
MANIFEST:=$(MANIFEST) \
         $(SNAP)/lib/libstdc++.6.dylib \
         $(SNAP)/lib/libgcc_s.1.0.dylib
LIB_INSTALL=libstdc++.6.dylib libgcc_s.1.0.dylib
GCJ_STATIC=1
endif
ifeq ($(GCJ_VER),4)
MANIFEST:=$(MANIFEST) \
         $(SNAP)/lib/libgcj.6.dylib \
         $(SNAP)/lib/libstdc++.6.dylib \
         $(SNAP)/lib/libgcc_s.1.0.dylib
LIB_INSTALL=libgcj.6.dylib libstdc++.6.dylib libgcc_s.1.0.dylib
GCJ_STATIC=0
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
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).so
ifeq ($(GCJ_VER),3)
LIB_INSTALL=
GCJ_STATIC=1
endif
ifeq ($(GCJ_VER),4)
MANIFEST:=$(MANIFEST) \
         $(SNAP)/lib/libgcj.so.6 \
         $(SNAP)/lib/libstdc++.so.6 \
         $(SNAP)/lib/libgcc_s.so.1
LIB_INSTALL=libgcj.so.6 libstdc++.so.6 libgcc_s.so.1
GCJ_STATIC=0
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
            GCJ_HOME=$(GCJ_HOME) \
            GCJ_LIBDIR=$(GCJ_HOME)/lib \
            GCJ_STATIC=$(GCJ_STATIC) \
            LIB_INSTALL="$(LIB_INSTALL)" \
            PYDBG=$(PYDBG) \
            _SUFFIX=$(_SUFFIX) \
            CC=$(PYLUCENE_CC) \
            CXX=$(PYLUCENE_CXX) \
            JCC=$(PYLUCENE_JCC) \
            JCCH=$(PYLUCENE_JCCH) \
            DB=$(BUILD_ROOT)/db/db-$(DB_VER) \
            DB_VER=$(DB_VER) \
            DB_LIB_VER=$(DB_LIB_VER) \
            PREFIX_DB=$(PREFIX_DB) \
            BUILD_DB=$(BUILD_DB) \
            PYTHON_VER=$(PYTHON_VER) \
            VERSION=$(VERSION) \
            all install

test:
	$(MAKE) -C $(SRC) PYTHON=$(PYTHON) test

ifeq (/,$(SRC))
clean: $(SRC)
	$(MAKE) -C $(SRC) clean
	rm -f $(CHANDLERBIN)/$(SNAP)/$(TARBALL).inst
endif

binaries:
	tar -C $(BUILD_ROOT) -cvzf $(TARBALL) $(MANIFEST)

ifeq ($(OS),Darwin)
ifeq ($(ARCH),i386)
PYLUCENE_SRC_ARCHIVE=PyLucene-src-$(VERSION)-darwin-i386.tar.gz
else
PYLUCENE_SRC_ARCHIVE=PyLucene-src-$(VERSION).tar.gz
endif
else
PYLUCENE_SRC_ARCHIVE=PyLucene-src-$(VERSION).tar.gz
endif

sources: $(PYLUCENE_SRC_ARCHIVE)

$(PYLUCENE_SRC_ARCHIVE):
	$(CURL) http://builds.osafoundation.org/external/$(PYLUCENE_SRC_ARCHIVE)

PyLucene-src-$(VERSION)-expanded: $(PYLUCENE_SRC_ARCHIVE)
	tar xvzf $(PYLUCENE_SRC_ARCHIVE)
	touch PyLucene-src-$(VERSION)-expanded

expand: PyLucene-src-$(VERSION)-expanded

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)

.PHONY: dummy

dummy:
	cp -p dummy/PyLucene.py $(CHANDLERBIN)/$(BUILD)/$(SITE)/PyLucene.py
