
VERSION=2.2.0-2-$(SVNVER)
SVNVER=367
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PYLUCENE=$(BUILD_ROOT)/PyLucene
SRC=$(PYLUCENE)/PyLucene-$(VERSION)
BUILD=$(SNAP)
TARBALL=PyLucene-$(SNAP)-$(RELVER).tar.gz
MANIFEST=$(SNAP)/$(SITE)/lucene

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Darwin)

ifeq ($(MACOSX_DEPLOYMENT_TARGET),10.3)
NUM_FILES=8
else
NUM_FILES=1
endif

ANT=ant
JCC_ENV=
ENV=

ifeq ($(DEBUG),1)
DEBUG_OPT=--debug
endif

endif

ifeq ($(OS),Linux)

ifeq ($(ARCH),x86_64)
NUM_FILES=2
arch=amd64
vm=server
else
NUM_FILES=1
arch=i386
vm=client
endif

JDK=$(BUILD_ROOT)/openjdk/j2sdk-image
JRE=$(BUILD_ROOT)/openjdk/j2re-image
ANT="$(BUILD_ROOT)/openjdk/apache-ant-1.7.0/bin/ant"
JCC_ENV=\
  JCC_INCLUDES="$(JDK)/include:$(JDK)/include/linux" \
  JCC_LFLAGS="-L$(JDK)/jre/lib/$(arch):-ljava"
ENV=\
  LD_LIBRARY_PATH="$(JRE)/lib/$(arch):$(JRE)/lib/$(arch)/$(vm):$(LD_LIBRARY_PATH)" \
  JAVA_HOME="$(JDK)"

ifeq ($(DEBUG),1)
DEBUG_OPT=--debug
endif

endif

ifeq ($(OS),Cygwin)

NUM_FILES=2
JDK=$(BUILD_ROOT)/openjdk/j2sdk-image
JRE=$(BUILD_ROOT)/openjdk/j2re-image
ANT="$(BUILD_ROOT)/openjdk/apache-ant-1.7.0/bin/ant"
JCC_ENV=\
  JCC_INCLUDES=`cygpath -awp "$(JDK)/include:$(JDK)/include/win32"` \
  JCC_LFLAGS="/LIBPATH:"`cygpath -awp "$(JDK)/lib:jvm.lib"`
ENV=\
  PATH="$(JRE)/bin:$(JRE)/bin/client:$(PATH)" \
  JAVA_HOME=`cygpath -aw "$(JDK)"`

ifeq ($(DEBUG),1)
ENV:=$(ENV) \
  CFLAGS=/Od /DPy_DEBUG=1
DEBUG_OPT=--debug
endif

endif

PyLucene-$(VERSION)-expanded:
	svn export -r $(SVNVER) http://svn.osafoundation.org/pylucene/trunk/jcc PyLucene-$(VERSION)
	touch PyLucene-$(VERSION)-expanded

expand: PyLucene-$(VERSION)-expanded

sources: expand

clean:
	rm -rf $(SRC)/jcc/build
	$(ENV) $(MAKE) -C $(SRC) ANT=$(ANT) clean

build: expand
	rm -rf $(SRC)/jcc/build
	rm -rf $(SRC)/build
	cd $(SRC)/jcc; $(ENV) $(JCC_ENV) \
                       $(PYTHON) setup.py build $(DEBUG_OPT) install
	$(ENV) $(MAKE) -C $(SRC) \
            PYTHON="$(PYTHON)" \
            ANT=$(ANT) \
            JCC="$(PYTHON) -m jcc" \
            NUM_FILES=$(NUM_FILES) \
            DEBUG=$(DEBUG) \
          compile install

test:
	$(ENV) $(MAKE) -C $(SRC) \
            PYTHON="$(PYTHON)" \
            ANT=$(ANT) \
            JCC="$(PYTHON) -m jcc" \
            NUM_FILES=$(NUM_FILES) \
            DEBUG=$(DEBUG) \
          test

$(TARBALL):
	tar -C $(BUILD_ROOT) -cvzf $(TARBALL) $(MANIFEST)

binaries: $(TARBALL)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)
