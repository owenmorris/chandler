
VERSION=0.9.9-192
RELVER=$(VERSION)-1
PYLUCENE=$(BUILD_ROOT)/PyLucene
SRC=$(PYLUCENE)/PyLucene-$(VERSION)

DB_VER=4.3.27
DB_LIB_VER=$(basename $(DB_VER))

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)
ifeq ($(DEBUG),1)
SUFFIX=d
_SUFFIX=_d
PYDBG=-DPy_DEBUG=1
else
SUFFIX=
_SUFFIX=
endif
PREFIX_PYTHON=$(PREFIX)/bin
PREFIX_DB=$(BUILD_ROOT)/persistence/db/db-$(DB_VER)
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
ifeq ($(DB_LIB_VER),4.3)
_dylib=dylib
else
_dylib=jnilib
endif
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).$(_dylib) \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).la \
         $(SNAP)/lib/libgcj.$(LIBGCJ_VER).dylib
ifeq ($(GCJ_VER),3)
MANIFEST=$(MANIFEST) \
         $(SNAP)/lib/libgcc_s.1.0.dylib \
         $(SNAP)/lib/libstdc++.6.dylib
endif
else

ifeq ($(OS),Linux)
PREFIX_PYTHON=$(PREFIX)
PREFIX_DB=$(PREFIX)/db
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/db/lib/libdb_java-$(DB_LIB_VER).so \
         $(SNAP)/lib/libgcj.so.$(LIBGCJ_VER)
ifeq ($(GCJ_VER),3)
MANIFEST=$(MANIFEST) \
         $(SNAP)/lib/libgcc_s.so.1 \
         $(SNAP)/lib/libstdc++.so.6
endif
endif
endif
endif


apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok


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

ifeq ($(PYLUCENE_JAR),)
ifeq ($(GCJ_VER),3)
PYLUCENE_JAR=$(GCJ_HOME)/bin/jar
endif
ifeq ($(GCJ_VER),4)
PYLUCENE_JAR=$(GCJ_HOME)/bin/fastjar
endif
endif

build: expand apply
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            SWIG=$(SWIG) \
            GCJ_HOME=$(GCJ_HOME) \
            GCJ_VER=$(GCJ_VER) \
            PYDBG=$(PYDBG) \
            CC=$(PYLUCENE_CC) \
            CXX=$(PYLUCENE_CXX) \
            JCC=$(PYLUCENE_JCC) \
            JCCH=$(PYLUCENE_JCCH) \
            JAR=$(PYLUCENE_JAR) \
            DB=$(BUILD_ROOT)/persistence/db/db-$(DB_VER) \
            DB_VER=$(DB_VER) \
            DB_LIB_VER=$(DB_LIB_VER) \
            PREFIX_DB=$(PREFIX_DB) \
            BUILD_DB=build_$(SNAP) \
            PYTHON_VER=$(PYTHON_VER) \
            VERSION=$(VERSION) \
            all install

clean:
	$(MAKE) -C $(SRC) clean

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYLUCENE)/pylucene-$(SNAP)-$(RELVER).tar.gz $(MANIFEST); \
	$(MD5) $(PYLUCENE)/pylucene-$(SNAP)-$(RELVER).tar.gz > $(PYLUCENE)/pylucene-$(SNAP)-$(RELVER).tar.gz.md5

install: pylucene-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf pylucene-$(SNAP)-$(RELVER).tar.gz

upload: $(PYLUCENE)/pylucene-$(SNAP)-$(RELVER).tar.gz
	scp $(PYLUCENE)/pylucene-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp $(PYLUCENE)/pylucene-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

PyLucene-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/PyLucene-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/PyLucene-$(VERSION).tar.gz.md5

sources: PyLucene-$(VERSION).tar.gz

PyLucene-$(VERSION)-expanded: PyLucene-$(VERSION).tar.gz
	tar xvzf PyLucene-$(VERSION).tar.gz
	touch PyLucene-$(VERSION)-expanded

expand: PyLucene-$(VERSION)-expanded
