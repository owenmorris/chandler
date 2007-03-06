
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/ or internal/

.PHONY: default install-core install distrib clean download downloads \
	plugins no-plugins distrib-plugins rst docs archives

default: install

BUILD_PLUGINS = Chandler-HelloWorldPlugin \
                Chandler-AmazonPlugin \
                Chandler-EVDBPlugin \
                Chandler-EventLoggerPlugin \
                Chandler-FeedsPlugin \
                Chandler-PhotoPlugin \
                Chandler-FlickrPlugin \
                Chandler-I18nTestsPlugin \
                Chandler-p2pPlugin

# When a version changes, the ARCHIVES lists below need to be updated.

ARCHIVES = \
    $(CHANDLERARCHIVES)/Launchers-$(SNAP)-0.9-$(BP)10.tar.gz \
    $(CHANDLERARCHIVES)/chandlerdb-$(SNAP)-0.6-$(BP)83.tar.gz \
    $(CHANDLERARCHIVES)/db-$(SNAP)-4.5.20-$(BP)3.tar.gz \
    $(CHANDLERARCHIVES)/python-$(SNAP)-2.5-$(BP)4.tar.gz \
    $(CHANDLERARCHIVES)/epydoc-$(SNAP)-2.1-$(BP)10.tar.gz \
    $(CHANDLERARCHIVES)/icu-$(SNAP)-3.6-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/openssl-$(SNAP)-0.9.8d-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/m2crypto-$(SNAP)-514-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/pychecker-$(SNAP)-0.8.17-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/PyICU-$(SNAP)-0.6-70-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/PyLucene-$(SNAP)-2.0.0-7-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/twisted-$(SNAP)-r18795-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/wxPython-$(SNAP)-2.8.1.1-r157-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/dateutil-$(SNAP)-1.1-$(BP)4.tar.gz \
    $(CHANDLERARCHIVES)/vobject-$(SNAP)-0.4.8-r182-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/zanshin-$(SNAP)-163-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/logilab-astng-$(SNAP)-0.16.3-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/logilab-common-$(SNAP)-0.21.0-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/pylint-$(SNAP)-0.12.2-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/parsedatetime-$(SNAP)-0.8.3-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/configobj-$(SNAP)-4.3.2-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/docutils-$(SNAP)-0.4-$(BP)1.tar.gz \
    $(CHANDLERARCHIVES)/eggtranslations-$(SNAP)-0.1-r2-$(BP)2.tar.gz \
    $(CHANDLERARCHIVES)/zope.interface-$(SNAP)-3.3.0b2-r71371-$(BP)3.tar.gz \
    $(CHANDLERARCHIVES)/setuptools-$(SNAP)-0.6c6dev-r54072-$(BP)1.tar.gz

OS         = $(shell uname)
PYTHON_VER = 2.5
BP         = 

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
    OS = Cygwin
endif

ifeq ($(findstring WINNT,$(OS)),WINNT)
    OS = Cygwin
endif

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

PLUGIN_ARCHIVES = $(CHANDLERARCHIVES)

ifeq ($(OS),Cygwin)
    SITE       = $(SNAP)/bin/Lib/site-packages
    PLATFORM   = windows
    SCRIPTS    = $(C_BIN)/$(SNAP)/bin/Scripts/
    RUN_PYTHON = CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(C_BIN)/$(SNAP)/RunPython.bat
    SED_MODERN = -r
else
    ifeq ($(OS),Darwin)
        FRAMEWORK  = Library/Frameworks/Python.framework/Versions/$(PYTHON_VER)
        SITE       = $(SNAP)/$(FRAMEWORK)/lib/python$(PYTHON_VER)/site-packages
        ARCH       = $(shell arch)
        SCRIPTS    = $(C_BIN)/$(SNAP)/$(FRAMEWORK)/bin/
        RUN_PYTHON = MACOSX_DEPLOYMENT_TARGET= CHANDLERHOME=$(CHANDLERHOME) $(C_BIN)/$(SNAP)/RunPython
        SED_MODERN = -E

        ifeq ($(ARCH),ppc)
            PLATFORM = macosx
        else
            PLATFORM = maciosx
        endif
    else
        SITE       = $(SNAP)/lib/python$(PYTHON_VER)/site-packages
        PLATFORM   = linux
        SCRIPTS    = $(C_BIN)/$(SNAP)/bin/
        RUN_PYTHON = CHANDLERHOME=$(CHANDLERHOME) $(C_BIN)/$(SNAP)/RunPython
        SED_MODERN = -r
    endif
endif

# readline is only needed for OS X
# use PLATFORM so this target can be run on another OS
ifeq ($(PLATFORM),macosx)
    ARCHIVES += $(CHANDLERARCHIVES)/readline-$(SNAP)-5.2-$(BP)1.tar.gz
endif
ifeq ($(PLATFORM),maciosx)
    ARCHIVES += $(CHANDLERARCHIVES)/readline-$(SNAP)-5.2-$(BP)1.tar.gz
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
TOOLS       = $(C_HOME)/tools/

#
# The following cygpaths are all done using
# := (or 'simply expanded') to prevent errant
# \ escaping that occurs when = is used
#
ifeq ($(OS),Cygwin)
    PLUGIN_INST := $(shell cygpath -aw $(PLUGIN_INST))
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

chandler-locale-data:
	$(RUN_PYTHON) setup.py egg_info

$(ARCHIVES):
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ $(P_URL)/$(notdir $@)

$(ARCHIVES_INST):
	tar -C $(C_BIN) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@))
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

install-core: archives manifest_exe chandler-locale-data 

plugins: $(addprefix develop-, $(BUILD_PLUGINS))

no-plugins: $(addprefix develop-u-, $(BUILD_PLUGINS))

distrib-plugins: $(addprefix develop-u-, $(BUILD_PLUGINS)) \
                 $(addprefix install-, $(BUILD_PLUGINS))

install: install-core plugins

distrib: install-core distrib-plugins

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

docs: rst

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
	CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(C_HOME)/tools/do_tests.sh -u

distclean:
	rm -rf $(C_BIN)/$(SNAP)
	rm -f  $(PLUGIN_INST)/*.egg-link
	rm -f  $(PLUGIN_INST)/*.pth
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

relocatable-starters:
	$(MAKE) -C distrib/relocatable \
                DSTDIR=`pwd`/relocatable \
                starters

relocatable-archive:
	$(MAKE) -C distrib/relocatable \
                DSTDIR=`pwd`/relocatable \
                archive
