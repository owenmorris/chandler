
VERSION=0.8.2
RELVER=$(VERSION)-4
PYLUCENE=$(BUILD_ROOT)/PyLucene
SRC=$(PYLUCENE)/PyLucene-$(VERSION)

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
PREFIX_DB=$(BUILD_ROOT)/persistence/db/db-4.2.52
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene$(_SUFFIX).pyd \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/bin/libdb_java42$(SUFFIX).dll
else

ifeq ($(OS),Darwin)
PREFIX_PYTHON=$(PREFIX)/$(FRAMEWORK)
PREFIX_DB=$(PREFIX)/db
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/db/lib/libdb_java-4.2.jnilib \
         $(SNAP)/db/lib/libdb_java-4.2.la \
         $(SNAP)/lib/libgcc_s.1.0.dylib \
         $(SNAP)/lib/libgcj.5.dylib \
         $(SNAP)/lib/libstdc++.6.dylib
else

ifeq ($(OS),Linux)
PREFIX_PYTHON=$(PREFIX)
PREFIX_DB=$(PREFIX)/db
MANIFEST=$(SNAP)/$(SITE)/PyLucene.py \
         $(SNAP)/$(SITE)/_PyLucene.so \
         $(SNAP)/$(SITE)/security/classpath.security \
         $(SNAP)/$(SITE)/security/libgcj.security \
         $(SNAP)/db/lib/libdb_java-4.2.so \
         $(SNAP)/lib/libgcc_s.so.1 \
         $(SNAP)/lib/libgcj.so.5 \
         $(SNAP)/lib/libstdc++.so.6
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
PYLUCENE_JAR=$(GCJ_HOME)/bin/jar
endif

build: expand apply
	$(MAKE) -C $(SRC) \
            PREFIX=$(PREFIX) \
            PREFIX_PYTHON=$(PREFIX_PYTHON) \
            SWIG=$(SWIG) \
            GCJ_HOME=$(GCJ_HOME) \
            CC=$(PYLUCENE_CC) \
            CXX=$(PYLUCENE_CXX) \
            JCC=$(PYLUCENE_JCC) \
            JCCH=$(PYLUCENE_JCCH) \
            JAR=$(PYLUCENE_JAR) \
            DB=$(BUILD_ROOT)/persistence/db/db-4.2.52 \
            PREFIX_DB=$(PREFIX_DB) \
            BUILD_DB=build_$(SNAP) \
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
