
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/ or internal/

.PHONY: default install-core install distrib clean download downloads build-plugins install-plugin-core rst docs archives

default: install

BUILD_PLUGINS = Chandler-HelloWorldPlugin \
                Chandler-AmazonPlugin \
                Chandler-EVDBPlugin \
                Chandler-EventLoggerPlugin \
                Chandler-FeedsPlugin \
                Chandler-FlickrPlugin \
                Chandler-I18nTestsPlugin \
                Chandler-PhotoPlugin \
                Chandler-p2pPlugin \
                EggTranslations-Plugin

PYEGGS = 

# When a version changes, the ARCHIVES lists below needs to be updated.
# these get installed into release or debug
ARCHIVES = $(CHANDLERARCHIVES)/Launchers-$(SNAP)-0.9-$(BP)3.tar.gz \
           $(CHANDLERARCHIVES)/chandlerdb-$(SNAP)-0.6-$(BP)72.tar.gz \
           $(CHANDLERARCHIVES)/db-$(SNAP)-4.5.20-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/python-$(SNAP)-2.5-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/epydoc-$(SNAP)-2.1-$(BP)10.tar.gz \
           $(CHANDLERARCHIVES)/icu-$(SNAP)-3.6-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/openssl-$(SNAP)-0.9.8d-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/m2crypto-$(SNAP)-0.17-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/pychecker-$(SNAP)-0.8.17-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/PyICU-$(SNAP)-0.6-66-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/PyLucene-$(SNAP)-2.0.0-7-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/twisted-$(SNAP)-r18795-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/wxPython-$(SNAP)-2.8.1.0-r137-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/zope.interface-$(SNAP)-3.3.0b2-r71371-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/dateutil-$(SNAP)-1.1-$(BP)4.tar.gz \
           $(CHANDLERARCHIVES)/vobject-$(SNAP)-0.4.5-r172-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/zanshin-$(SNAP)-158-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/logilab-astng-$(SNAP)-0.16.3-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/logilab-common-$(SNAP)-0.21.0-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/pylint-$(SNAP)-0.12.2-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/parsedatetime-$(SNAP)-0.8.0-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/configobj-$(SNAP)-4.3.2-$(BP)1.tar.gz

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
    SNAP         =release
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
    SITE          = $(SNAP)/bin/Lib/site-packages
    PLATFORM      = windows
    EASYINSTALL   = $(C_BIN)/$(SNAP)/easy_install.exe
    PLUGIN_PYTHON = CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(C_BIN)/$(SNAP)/bin/python$(DEBUG_SUFFIX)
    RUN_PYTHON    = CHANDLERHOME='$(CHANDLERHOME)' CHANDLERBIN='$(CHANDLERBIN)' $(C_BIN)/$(SNAP)/RunPython.bat
    SED_MODERN    = -r
else
    ifeq ($(OS),Darwin)
        FRAMEWORK     = Library/Frameworks/Python.framework/Versions/$(PYTHON_VER)
        SITE          = $(SNAP)/$(FRAMEWORK)/lib/python$(PYTHON_VER)/site-packages
        ARCH          = $(shell arch)
        EASYINSTALL   = MACOSX_DEPLOYMENT_TARGET= $(PYTHON_BIN) $(C_BIN)/$(SNAP)/easy_install
        PLUGIN_PYTHON = MACOSX_DEPLOYMENT_TARGET= CHANDLERHOME=$(CHANDLERHOME) $(C_BIN)/$(SNAP)/RunPython
        RUN_PYTHON    = $(C_BIN)/$(SNAP)/RunPython
        SED_MODERN    = -E

        ifeq ($(ARCH),ppc)
            PLATFORM = macosx
        else
            PLATFORM = maciosx
        endif
    else
        SITE          = $(SNAP)/lib/python$(PYTHON_VER)/site-packages
        PLATFORM      = linux
        EASYINSTALL   = $(C_BIN)/$(SNAP)/easy_install
        PLUGIN_PYTHON = CHANDLERHOME=$(CHANDLERHOME) $(C_BIN)/$(SNAP)/RunPython
        RUN_PYTHON    = $(C_BIN)/$(SNAP)/RunPython
        SED_MODERN    =-r
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
    CURL=curl $(CHANDLER_CURL_OPTIONS) -f -o
endif

HOST  = builds.osafoundation.org
URL   = http://$(HOST)/external
P_URL = $(URL)/$(PLATFORM)

SETUPTOOLS_EGG  = $(CHANDLERARCHIVES)/setuptools-0.6c4dev_r52887-py$(PYTHON_VER).egg
SETUPTOOLS_ABS  = $(SETUPTOOLS_EGG)
SETUPTOOLS_BIN  = $(C_BIN)/$(SNAP)
EASYINSTALL_BIN = $(EASYINSTALL)
PLUGIN_ABS      = $(PLUGIN_ARCHIVES)
PLUGIN_INST     = $(C_HOME)
PYEGG_INST      = $(C_BIN)/$(SITE)
PYTHON_BIN      = $(C_BIN)/$(SNAP)/RunPython
TOOLS           = $(C_HOME)/tools/
PYEGG_ARCHIVES  = $(CHANDLERARCHIVES)/

#
# The following cygpaths are all done using
# := (or 'simply expanded') to prevent errant
# \ escaping that occurs when = is used
#
ifeq ($(OS),Cygwin)
    PYTHON_BIN      := $(SETUPTOOLS_BIN)/bin/python$(DEBUG_SUFFIX)
    SETUPTOOLS_ABS  := $(shell cygpath -wa $(SETUPTOOLS_EGG))
    SETUPTOOLS_BIN  := $(shell cygpath -wa $(SETUPTOOLS_BIN))
    EASYINSTALL_BIN := $(shell cygpath -wa $(EASYINSTALL))
    PLUGIN_ABS      := $(shell cygpath -aw $(PLUGIN_ARCHIVES))
    PLUGIN_INST     := $(shell cygpath -aw $(C_HOME))
    PYEGG_INST      := $(shell cygpath -aw $(C_BIN)/$(SITE))
    TOOLS           := $(shell cygpath -aw $(TOOLS))\\
    PYEGG_ARCHIVES  := $(shell cygpath -aw $(CHANDLERARCHIVES))\\
endif

ARCHIVES_INST = \
    $(addsuffix .inst, \
                $(addprefix $(C_BIN)/$(SNAP)/, \
                            $(notdir $(ARCHIVES))))

PYEGGS_INST = \
    $(addsuffix .inst, \
                $(addprefix $(C_BIN)/$(SNAP)/, \
                            $(notdir $(PYEGGS))))

downloads: $(ARCHIVES)

$(addprefix binaries-, $(BUILD_PLUGINS)):
	cd $(C_HOME)/projects/$(subst binaries-,,$@); \
    PYTHONPATH='$(PLUGIN_INST)' $(PLUGIN_PYTHON) setup.py develop \
      --script-dir='$(SETUPTOOLS_BIN)' \
      --install-dir='$(PLUGIN_INST)'

#
# for distribution the egg develop mode has to be turned off
# and the egg installed in the normal manner
#
$(addprefix distrib-, $(BUILD_PLUGINS)):
	cd $(C_HOME)/projects/$(subst distrib-,,$@); \
    PYTHONPATH='$(PLUGIN_INST)' $(PLUGIN_PYTHON) setup.py develop -u \
      --script-dir='$(SETUPTOOLS_BIN)' \
      --install-dir='$(PLUGIN_INST)'
	cd $(C_HOME)/projects/$(subst distrib-,,$@); \
    PYTHONPATH='$(PLUGIN_INST)' $(PLUGIN_PYTHON) setup.py install \
      --install-scripts='$(SETUPTOOLS_BIN)' \
      --install-lib='$(PLUGIN_INST)'

#bdist_egg -d ../../$(CHANDLERARCHIVES)

build-plugins: $(addprefix binaries-, $(BUILD_PLUGINS))

distrib-plugins: $(addprefix distrib-, $(BUILD_PLUGINS))

chandler-locale-data:
	PYTHONPATH='$(PLUGIN_INST)' $(PLUGIN_PYTHON) setup.py egg_info

$(ARCHIVES):
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ $(P_URL)/$(notdir $@)

$(ARCHIVES_INST):
	tar -C $(C_BIN) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@))
	touch $@

$(PYEGGS):
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ $(P_URL)/$(notdir $@)

$(PYEGGS_INST):
	MACOSX_DEPLOYMENT_TARGET= PYTHONPATH='$(PLUGIN_INST)' \
      $(PYTHON_BIN) -c "from setuptools.command.easy_install import main; main()" \
      --script-dir='$(SETUPTOOLS_BIN)' \
      --install-dir='$(PYEGG_INST)' \
      '$(PYEGG_ARCHIVES)'$(notdir $(basename $@))
	touch $@

$(SETUPTOOLS_EGG):
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ $(P_URL)/$(notdir $@)

setuptools: $(SETUPTOOLS_EGG)
	MACOSX_DEPLOYMENT_TARGET= PYTHONPATH='$(PLUGIN_INST)' CHANDLERHOME='$(CHANDLERHOME)' $(PYTHON_BIN) \
      -c "import sys; sys.path.insert(0,r'$(SETUPTOOLS_ABS)'); from setuptools.command.easy_install import main; main()" \
      --script-dir='$(SETUPTOOLS_BIN)' \
      --install-dir='$(PLUGIN_INST)' \
      '$(SETUPTOOLS_ABS)'

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

install-core: archives manifest_exe

install-plugin-core: $(SETUPTOOLS_EGG) $(PYEGGS) setuptools chandler-locale-data $(PYEGGS_INST)

plugins: install-plugin-core build-plugins

install: install-core plugins

distrib: install-core install-plugin-core distrib-plugins

download: $(ARCHIVES) $(SETUPTOOLS_EGG) $(PYEGGS)

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
	rst2html.py --stylesheet=distrib/docs/rst-docs.css $< $@

distrib/docs/running-code-at-startup.html: parcels/osaf/startups.txt
	rst2html.py --stylesheet=distrib/docs/rst-docs.css $< $@

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

clean:
	rm -rf $(C_BIN)/$(SNAP)
	rm -rf __repository__
	rm -f chandler.log randpool.dat
	find . -name '*.py[co]' -delete

distclean: clean
	rm -rf $(C_BIN)/debug
	rm -rf $(C_BIN)/release
	rm -f  $(C_HOME)/*.egg-link
	rm -f  $(C_HOME)/*.pth
	rm -rf $(C_HOME)/*-py$(PYTHON_VER).egg

realclean: distclean
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
