# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/ or internal/

.PHONY: default install-core install distrib clean download downloads \
	plugins no-plugins distrib-plugins rst docs archives

default: install

OS           = $(shell uname)
OS_VER       = $(shell uname -r)
OS_MAJOR_VER = $(firstword $(subst ., ,$(OS_VER)))
PYTHON_VER   = 2.5
BP           =
LOCALE_VER   = trunk

BUILD_PLUGINS = Chandler-HelloWorldPlugin \
                Chandler-AmazonPlugin \
                Chandler-EVDBPlugin \
                Chandler-EventLoggerPlugin \
                Chandler-FeedsPlugin \
                Chandler-PhotoPlugin \
                Chandler-FlickrPlugin \
                Chandler-debugPlugin \
                Chandler-p2pPlugin \
                Chandler-gdataPlugin

BUILD_LOCALES = en \
                fr \
                fi \
                sv \
                de

ifeq ($(OS),Darwin)
    ifeq ($(shell arch),ppc)
        PLATFORM = macosx
    else
        PLATFORM = maciosx
    endif
    ifeq ($(OS_MAJOR_VER),9)
        PLATFORM := $(PLATFORM)/10.5
    endif
endif

ifeq ($(OS),Linux)
    PLATFORM         = linux
    ARCH             = $(shell uname -m)
    DISTRIB_CODENAME = $(subst DISTRIB_CODENAME=,,$(shell cat /etc/lsb-release | grep DISTRIB_CODENAME))

    ifneq ($(findstring $(DISTRIB_CODENAME),feisty gutsy hardy intrepid jaunty),)
        PLATFORM := $(PLATFORM)/$(DISTRIB_CODENAME)
    endif
    ifeq ($(ARCH),x86_64)
        PLATFORM := $(PLATFORM)/$(ARCH)
    endif
endif

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
    OS       = Cygwin
    PLATFORM = windows
endif

ifeq ($(findstring WINNT,$(OS)),WINNT)
    OS       = Cygwin
    PLATFORM = windows
endif

# When a version changes, the ARCHIVES lists below need to be updated.

READLINE   = $(CHANDLERARCHIVES)/readline-$(SNAP)-5.2-$(BP)2.tar.gz
PYTHON     = $(CHANDLERARCHIVES)/python-$(SNAP)-2.5.1-$(BP)9.tar.gz
SETUPTOOLS = $(CHANDLERARCHIVES)/setuptools-$(SNAP)-0.6c6-$(BP)2.tar.gz
ICU        = $(CHANDLERARCHIVES)/icu-$(SNAP)-3.6-$(BP)2.tar.gz
OPENJDK    = $(CHANDLERARCHIVES)/openjdk-7-ea-j2re-b21-$(BP)3.tar.gz
OPENSSL    = $(CHANDLERARCHIVES)/openssl-$(SNAP)-0.9.8d-$(BP)3.tar.gz
CONFIGOBJ  = $(CHANDLERARCHIVES)/configobj-$(SNAP)-4.3.2-$(BP)2.tar.gz
DOCUTILS   = $(CHANDLERARCHIVES)/docutils-$(SNAP)-0.4-$(BP)2.tar.gz
ZOPE       = $(CHANDLERARCHIVES)/zope.interface-$(SNAP)-3.3.0b2-r71371-$(BP)4.tar.gz

ifeq ($(OS),Linux)
    READLINE =
    ifeq ($(PLATFORM),linux/feisty)
        PYTHON     =
        ICU        =
        CONFIGOBJ  =
        DOCUTILS   =
        ZOPE       =
    endif

    ifneq ($(findstring $(DISTRIB_CODENAME),gutsy hardy intrepid jaunty),)
        OPENSSL    =
        PYTHON     =
        ICU        =
        CONFIGOBJ  =
        DOCUTILS   =
        SETUPTOOLS =
        ZOPE       =
    endif

    ifeq ($(PLATFORM),linux/gutsy/x86_64)
        OPENJDK    = $(CHANDLERARCHIVES)/openjdk-7-ea-j2re-b23-$(BP)3.tar.gz
        OPENSSL    =
        PYTHON     =
        ICU        =
        CONFIGOBJ  =
        DOCUTILS   =
        SETUPTOOLS =
        ZOPE       =
    endif
endif

ifneq ($(findstring $(PLATFORM),macosx maciosx),)
    OPENJDK    =
endif

ifeq ($(findstring 10.5,$(PLATFORM)),10.5)
    PYTHON     =
    SETUPTOOLS =
    OPENJDK    =
    READLINE   =
endif

ifeq ($(PLATFORM),windows)
    READLINE   =
endif

ARCHIVES = \
    $(CHANDLERARCHIVES)/Launchers-$(SNAP)-0.9-$(BP)31.tar.gz \
    $(CHANDLERARCHIVES)/chandlerdb-$(SNAP)-0.7-$(BP)37.tar.gz \
    $(CHANDLERARCHIVES)/db-$(SNAP)-4.6.21-$(BP)3.tar.gz \
    $(READLINE) \
    $(PYTHON) \
    $(SETUPTOOLS) \
    $(ICU) \
    $(OPENSSL) \
    $(OPENJDK) \
    $(CHANDLERARCHIVES)/m2crypto-$(SNAP)-0.18.2-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/PyICU-$(SNAP)-0.8-92-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/PyLucene-$(SNAP)-2.3.1-3-418-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/twisted-$(SNAP)-r18795-$(BP)3.tar.gz \
    $(CHANDLERARCHIVES)/wxPython-$(SNAP)-2.8.7.1-r218-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/dateutil-$(SNAP)-1.1-$(BP)6.tar.gz \
    $(CHANDLERARCHIVES)/vobject-$(SNAP)-0.7.0-r206-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/zanshin-$(SNAP)-171-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/logilab-astng-$(SNAP)-0.17.0-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/logilab-common-$(SNAP)-0.21.2-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/pylint-$(SNAP)-0.13.1-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/parsedatetime-$(SNAP)-0.8.6-$(BP)1.tar.gz \
    $(CONFIGOBJ) \
    $(DOCUTILS) \
    $(CHANDLERARCHIVES)/epydoc-$(SNAP)-3.0beta1-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/eggtranslations-$(SNAP)-1.1-r10-$(BP)2.tar.gz \
    $(ZOPE)

ifeq ($(DEBUG),1)
    SNAP         = debug
    DEBUG_SUFFIX = _d
else
    SNAP         = release
    DEBUG_SUFFIX =
endif

# on Windows, CHANDLERHOME and CHANDLERBIN *must* be in Windows style
# this is because of RunChandler.bat and RunPython.bat
# so internally we need to convert them to unix style

ifeq ($(OS),Cygwin)
    ifeq ($(CHANDLERHOME),)
        C_HOME        = $(shell pwd)
        CHANDLERHOME := $(shell cygpath -aw $(C_HOME))
    else
        C_HOME        = $(shell cygpath -au '$(CHANDLERHOME)')
        CHANDLERHOME := $(shell cygpath -aw $(C_HOME))
    endif
    ifeq ($(CHANDLERBIN),)
        CHANDLERBIN := $(shell cygpath -aw '$(C_HOME)')
    else
        CHANDLERBIN := $(shell cygpath -aw '$(CHANDLERBIN)')
    endif

    C_BIN = $(shell cygpath -au '$(CHANDLERBIN)')
else
    ifeq ($(CHANDLERHOME),)
        CHANDLERHOME = $(shell pwd)
    endif
    ifeq ($(CHANDLERBIN),)
        CHANDLERBIN = $(CHANDLERHOME)
    endif

    C_BIN  = $(CHANDLERBIN)
    C_HOME = $(CHANDLERHOME)
endif

ifeq ($(CHANDLERARCHIVES),)
    CHANDLERARCHIVES = ../downloads
endif

ifeq ($(OS),Cygwin)
    SCRIPTS    = $(C_BIN)/$(SNAP)/bin/Scripts/
    RUN_PYTHON = CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(C_BIN)/$(SNAP)/RunPython.bat
    SED_MODERN = -r
endif

ifeq ($(OS),Darwin)
    ifeq ($(PYTHON),)
        SCRIPTS = $(SNAP)/bin/
    else
        SITE       = $(SNAP)/lib/python$(PYTHON_VER)/site-packages
        SCRIPTS    = $(C_BIN)/$(SNAP)/bin/
        RUN_PYTHON = CHANDLERHOME=$(CHANDLERHOME) $(C_BIN)/$(SNAP)/RunPython
        SED_MODERN = -r
    endif
    ARCH       = $(shell arch)
    RUN_PYTHON = MACOSX_DEPLOYMENT_TARGET= CHANDLERHOME=$(CHANDLERHOME) $(C_BIN)/$(SNAP)/RunPython
    SED_MODERN = -E
endif

ifeq ($(OS),Linux)
    ifeq ($(PYTHON),)
        SCRIPTS = $(SNAP)/bin/
    else
        SCRIPTS = $(C_BIN)/$(SNAP)/bin/
    endif
    RUN_PYTHON = CHANDLERHOME=$(CHANDLERHOME) $(C_BIN)/$(SNAP)/RunPython
    SED_MODERN = -r
endif

# We download some pretty big files, which can clog your network. You can now
# control the download options (well, any options) for curl. For example:
#   CHANDLER_CURL_OPTIONS="--limit-rate 200K"
#
# You can also replace curl with something else, for example wget:
#   CURL="wget -r -P .. -nd"

ifeq ($(CURL),)
    CURL=curl $(CHANDLER_CURL_OPTIONS) -f -L -o
endif

HOST  = builds.osafoundation.org
URL   = http://$(HOST)/external
P_URL = $(URL)/$(PLATFORM)

PLUGIN_INST = $(C_HOME)/plugins
LOCALE_SRC  = $(C_HOME)/localizations/
TOOLS       = $(C_HOME)/tools/

# The following cygpaths are all done using
# := (or 'simply expanded') to prevent errant
# \ escaping that occurs when = is used

ifeq ($(OS),Cygwin)
    PLUGIN_INST := $(shell cygpath -aw $(PLUGIN_INST))
    LOCALE_SRC  := $(shell cygpath -aw $(LOCALE_SRC))\\
    TOOLS       := $(shell cygpath -aw $(TOOLS))\\
    SCRIPTS     := $(shell cygpath -wa $(SCRIPTS))\\
endif

ARCHIVES_INST = \
    $(addsuffix .inst, \
                $(addprefix $(C_BIN)/$(SNAP)/, \
                            $(notdir $(ARCHIVES))))

downloads: $(ARCHIVES)

$(addprefix develop-, $(BUILD_PLUGINS)):
	mkdir -p '$(PLUGIN_INST)'
	cd $(C_HOME)/projects/$(subst develop-,,$@); \
     $(RUN_PYTHON) setup.py develop -m \
          --egg-path='../projects/$(subst develop-,,$@)' \
          --script-dir='$(PLUGIN_INST)' \
          --install-dir='$(PLUGIN_INST)'

$(addprefix develop-u-, $(BUILD_PLUGINS)):
	mkdir -p '$(PLUGIN_INST)'
	cd $(C_HOME)/projects/$(subst develop-u-,,$@); \
     $(RUN_PYTHON) setup.py develop -m -u \
          --egg-path='../projects/$(subst develop-u-,,$@)' \
          --script-dir='$(PLUGIN_INST)' \
          --install-dir='$(PLUGIN_INST)'

$(addprefix install-, $(BUILD_PLUGINS)):
	mkdir -p '$(PLUGIN_INST)'
	cd $(C_HOME)/projects/$(subst install-,,$@); \
     $(RUN_PYTHON) setup.py easy_install -m \
          --script-dir='$(PLUGIN_INST)' \
          --install-dir='$(PLUGIN_INST)' .

$(addprefix install-, $(BUILD_LOCALES)):
	mkdir -p '$(PLUGIN_INST)'
	rm -rf $(C_HOME)/localizations/$(subst install-,,$@)
	svn export http://svn.osafoundation.org/localizations/chandler/$(LOCALE_VER)/$(subst install-,,$@) localizations/$(subst install-,,$@)
	$(RUN_PYTHON) tools/createTranslationEgg.py -c --dist \
                  -l $(subst install-,,$@) \
                  -f '$(LOCALE_SRC)'$(subst install-,,$@)/Chandler-$(subst install-,,$@).po \
                  -d '$(LOCALE_SRC)'
	$(RUN_PYTHON) -m easy_install -x -m --install-dir='$(PLUGIN_INST)' '$(LOCALE_SRC)'Chandler.$(subst install-,,$@)-1.0-py$(PYTHON_VER).egg

chandler-locale-data:
	$(RUN_PYTHON) setup.py egg_info

$(ARCHIVES):
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ $(P_URL)/$(notdir $@)

# if the archive name does not contain the string 'release' or 'debug' it's
# the same for both and needs to be installed in $(SNAP) explicitely
$(ARCHIVES_INST):
	@if [ $(shell echo $(notdir $@) | sed "s/-$(SNAP)[^ ]*//g") = $(notdir $@) ]; then \
            echo tar -C $(C_BIN)/$(SNAP) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@)); \
            tar -C $(C_BIN)/$(SNAP) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@)); \
        else \
            echo tar -C $(C_BIN) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@)); \
            tar -C $(C_BIN) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@)); \
        fi
	touch $@

ifeq ($(OS),Cygwin)
manifest_exe:
	if [ -f "$(C_BIN)/$(SNAP)/bin/chandler.exe.manifest" ]; \
	then \
	    chmod +x $(C_BIN)/$(SNAP)/bin/chandler.exe.manifest; \
	fi
else
manifest_exe:
endif

archives: $(ARCHIVES) $(ARCHIVES_INST)

install-core: archives manifest_exe chandler-locale-data install-locales

install-locales: $(addprefix install-, $(BUILD_LOCALES))

plugins: $(addprefix develop-, $(BUILD_PLUGINS))

no-plugins: $(addprefix develop-u-, $(BUILD_PLUGINS))

distrib-plugins: $(addprefix develop-u-, $(BUILD_PLUGINS)) \
                 $(addprefix install-, $(BUILD_PLUGINS))

# On Ubuntu Feisty Fawn and Gutsy Gibbon users need to install some packages,
# check that we have them:
ifeq ($(OS),Linux)
ifeq ($(PLATFORM),linux/feisty)
py-env:
	@echo Checking that you have required packages installed...
	python -c "from pkg_resources import require; require('configobj >= 4.3.2')"
	python -c "from pkg_resources import require; require('zope.interface >= 0')"
else
ifneq ($(findstring $(DISTRIB_CODENAME),gutsy hardy intrepid jaunty),)
py-env:
	@echo Checking that you have required packages installed...
	python -c "from pkg_resources import require; require('setuptools >= 0.6c6')"
	python -c "from pkg_resources import require; require('configobj >= 4.3.2')"
	python -c "from pkg_resources import require; require('zope.interface >= 0')"
else
py-env:
endif
endif
else
py-env:
endif

install: install-core py-env plugins

install-no-plugins: install-core py-env

distrib: install-core py-env distrib-plugins

download: $(ARCHIVES)

# to install individual binaries, for example: make chandlerdb

$(notdir $(shell echo $(ARCHIVES) | sed "s/-$(SNAP)[^ ]*//g")):
	$(MAKE) $(shell echo $(ARCHIVES) | sed "s=.*\($(CHANDLERARCHIVES)/$@-[^ ]*\).*=\1=")
	$(MAKE) $(shell echo $(ARCHIVES_INST) | sed "s=.*\($(C_BIN)/$(SNAP)/$@-[^ ]*\).*=\1=")


ifeq ($(OS),Cygwin)
strip:
else
ifeq ($(DEBUG),1)
strip:
else
ifeq ($(OS),Darwin)
STRIP_OPTIONS=-S -x
STRIP_OP=\( -name '*.dylib' -o -name '*.so' \)
else
STRIP_OPTIONS=
STRIP_OP=-name '*.so'
endif
strip:
	find $(C_BIN)/release $(STRIP_OP) | xargs chmod +w
	find $(C_BIN)/release $(STRIP_OP) | xargs strip $(STRIP_OPTIONS)
endif
endif

RST_DOCS = distrib/docs/parcel-schema-guide.html \
           distrib/docs/running-code-at-startup.html

distrib/docs/parcel-schema-guide.html: application/parcel-schema-guide.txt
	$(RUN_PYTHON) '$(SCRIPTS)'rst2html.py --stylesheet=distrib/docs/rst-docs.css $< $@

distrib/docs/running-code-at-startup.html: parcels/osaf/startups.txt
	$(RUN_PYTHON) '$(SCRIPTS)'rst2html.py --stylesheet=distrib/docs/rst-docs.css $< $@

rst: $(RST_DOCS)

api:
	CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(RUN_PYTHON) '$(TOOLS)'gen_docs.py

docs: rst api

debug:
	CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(MAKE) DEBUG=1 install

purge:
	CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(RUN_PYTHON) '$(TOOLS)'purge.py .

check:
	CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(RUN_PYTHON) '$(TOOLS)'checker.py

lint:
	CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(RUN_PYTHON) '$(TOOLS)'lint.py

print-%:
	@echo $* = $($*)

tests:
	CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(C_HOME)/tools/rt.py -m $(SNAP) -u

distclean:
	rm -rf $(C_BIN)/$(SNAP)
	rm -f  $(PLUGIN_INST)/*.egg-link
	rm -f  $(PLUGIN_INST)/*.pth
	rm -rf $(PLUGIN_INST)/*.egg
	rm -rf $(C_HOME)/*-py$(PYTHON_VER).egg

clean: distclean
	find . -name '*.py[co]' -delete

realclean: clean
	rm -rf $(C_BIN)/release
	rm -rf $(C_BIN)/debug
	rm -f $(ARCHIVES)

relocatable-distro:
	$(MAKE) -C distrib/relocatable \
                DSTDIR=`pwd`/relocatable \
                SVNURL=`svn info | grep URL | sed 's/URL: //'` \
                distro

relocatable-deploy:
	$(MAKE) -C distrib/relocatable \
                DSTDIR=`pwd`/relocatable \
                SVNURL=`svn info | grep URL | sed 's/URL: //'` \
                deploy

relocatable-starters:
	$(MAKE) -C distrib/relocatable \
                DSTDIR=`pwd`/relocatable \
                starters

relocatable-archive:
	$(MAKE) -C distrib/relocatable \
                DSTDIR=`pwd`/relocatable \
                archive
