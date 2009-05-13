
VERSION=2.3.1-3-$(SVNVER)
SVNVER=418
PYLUCENE_SVN=http://svn.osafoundation.org/pylucene/branches/release-2.3 
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)1
PYLUCENE=$(BUILD_ROOT)/PyLucene
SRC=$(PYLUCENE)/PyLucene-$(VERSION)
BUILD=$(SNAP)
EGG=$(notdir $(shell cd $(BUILD_ROOT); find $(SNAP)/$(SITE) -name 'lucene-*-py$(PYTHON_VER)-*.egg'))
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

ifeq ($(findstring $(DISTRIB_CODENAME), hardy intrepid jaunty),)
JDK=$(BUILD_ROOT)/openjdk/j2sdk-image
JRE=$(BUILD_ROOT)/openjdk/j2re-image
ANT="$(BUILD_ROOT)/openjdk/apache-ant-1.7.0/bin/ant"
else
JDK=/usr/lib/jvm/java-6-openjdk
JRE=/usr/lib/jvm/java-6-openjdk/jre
ANT=/usr/bin/ant
endif
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

INSTALL_JCC_FLAGS =

ifeq ($(PYTHON_BUILD),)
    INSTALL_JCC_FLAGS = --prefix $(BUILD_ROOT)/$(SNAP)
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
DEBUG_OPT=--debug
endif

endif

PyLucene-$(VERSION)-expanded:
	svn export -r $(SVNVER) $(PYLUCENE_SVN) PyLucene-$(VERSION)
	touch PyLucene-$(VERSION)-expanded

expand: PyLucene-$(VERSION)-expanded

sources: expand

clean:
	rm -rf $(SRC)/jcc/build
	rm -rf $(SRC)/build
	find $(PREFIX) -name '*lucene*' | xargs rm -rf

build: expand
	rm -rf $(SRC)/jcc/build
	rm -rf $(SRC)/build
	cd $(SRC)/jcc; $(ENV) $(JCC_ENV) \
                       $(PYTHON) setup.py build $(DEBUG_OPT) install $(INSTALL_JCC_FLAGS)
	$(ENV) $(MAKE) -C $(SRC) \
            PYTHON="$(PYTHON)" \
            ANT=$(ANT) \
            JCC="$(PYTHON) -m jcc.__init__" \
            NUM_FILES=$(NUM_FILES) \
            DEBUG=$(DEBUG) \
          compile install

test:
	$(ENV) $(MAKE) -C $(SRC) \
            PYTHON="$(PYTHON)" \
            ANT=$(ANT) \
            JCC="$(PYTHON) -m jcc.__init__" \
            NUM_FILES=$(NUM_FILES) \
            DEBUG=$(DEBUG) \
          test

$(TARBALL):
	echo "./$(EGG)" > $(BUILD_ROOT)/$(SNAP)/$(SITE)/lucene.pth
	tar -C $(BUILD_ROOT) -cvzf $(PYLUCENE)/$(TARBALL) \
                             $(SNAP)/$(SITE)/$(EGG) \
                             $(SNAP)/$(SITE)/lucene.pth

binaries: $(TARBALL)

install: $(TARBALL)
	cp -p $(TARBALL) $(CHANDLERARCHIVES)
