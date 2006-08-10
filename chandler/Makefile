
# This Makefile requires cygwin on Windows
# It should *not* be made to depend on external/ or internal/


.PHONY: default install clean realclean downloads build-plugins

default: install


OS         = $(shell uname)
PYTHON_VER = 2.4
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

ifeq ($(CHANDLERHOME),)
    CHANDLERHOME = $(shell pwd)
endif

ifeq ($(CHANDLERBIN),)
    CHANDLERBIN = $(CHANDLERHOME)
endif

ifeq ($(CHANDLERARCHIVES),)
    CHANDLERARCHIVES = ../downloads
endif

PLUGIN_ARCHIVES = $(CHANDLERARCHIVES)

ifeq ($(OS),Cygwin)
    C_BIN         = $(shell cygpath -aw $(CHANDLERBIN))
    C_HOME        = $(shell cygpath -aw $(CHANDLERHOME))
    SITE          = $(SNAP)/bin/Lib/site-packages
    PLATFORM      = windows
    EASYINSTALL   = $(CHANDLERBIN)/$(SNAP)/easy_install.exe
    PLUGIN_PYTHON = CHANDLERHOME=$(shell cygpath -aw $(C_HOME)) $(CHANDLERBIN)/$(SNAP)/bin/python$(DEBUG_SUFFIX)
    SED_MODERN    = -r
else
    C_BIN  = $(CHANDLERBIN)
    C_HOME = $(CHANDLERHOME)

    ifeq ($(OS),Darwin)
        FRAMEWORK     = Library/Frameworks/Python.framework/Versions/$(PYTHON_VER)
        SITE          = $(SNAP)/$(FRAMEWORK)/lib/python$(PYTHON_VER)/site-packages
        ARCH          = $(shell arch)
        EASYINSTALL   = MACOSX_DEPLOYMENT_TARGET= $(PYTHON_BIN) $(C_BIN)/$(SNAP)/easy_install
        PLUGIN_PYTHON = MACOSX_DEPLOYMENT_TARGET= CHANDLERHOME=$(C_HOME) $(C_BIN)/$(SNAP)/RunPython
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
        PLUGIN_PYTHON = CHANDLERHOME=$(C_HOME) $(C_BIN)/$(SNAP)/RunPython
        SED_MODERN    =-r
    endif
endif


BUNDLED_PLUGINS = Chandler_HelloWorldPlugin-0.1-py2.4.egg \
                  Chandler_FeedsPlugin-0.2_r11264-py2.4.egg
#                  Chandler_FeedsPlugin-0.2_r11338-py2.4.egg
#                  EggTranslations_Plugin-0.1-py2.4.egg

BUILD_PLUGINS = Chandler-HelloWorldPlugin \
                Chandler-FeedsPlugin
#                EggTranslations-Plugin

# When a version changes, the ARCHIVES lists below needs to be updated.
# these get installed into release or debug
ARCHIVES = $(CHANDLERARCHIVES)/Launchers-$(SNAP)-0.8-$(BP)B.tar.gz \
           $(CHANDLERARCHIVES)/chandlerdb-$(SNAP)-0.6-$(BP)35.tar.gz \
           $(CHANDLERARCHIVES)/db-$(SNAP)-4.4.20-$(BP)5.tar.gz \
           $(CHANDLERARCHIVES)/python-$(SNAP)-2.4.3-$(BP)3.tar.gz \
           $(CHANDLERARCHIVES)/epydoc-$(SNAP)-2.1-$(BP)9.tar.gz \
           $(CHANDLERARCHIVES)/icu-$(SNAP)-3.4-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/openssl-$(SNAP)-0.9.8b-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/m2crypto-$(SNAP)-458-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/pychecker-$(SNAP)-0.8.13-$(BP)6.tar.gz \
           $(CHANDLERARCHIVES)/PyICU-$(SNAP)-0.5-62-$(BP)5.tar.gz \
           $(CHANDLERARCHIVES)/PyLucene-$(SNAP)-2.0.0-1-$(BP)2.tar.gz \
           $(CHANDLERARCHIVES)/twisted-$(SNAP)-r15399-$(BP)4.tar.gz \
           $(CHANDLERARCHIVES)/wxPython-$(SNAP)-2.7.0.0-r71-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/zopeinterface-$(SNAP)-3.1.0c1-$(BP)4.tar.gz \
           $(CHANDLERARCHIVES)/dateutil-$(SNAP)-1.1-$(BP)3.tar.gz \
           $(CHANDLERARCHIVES)/vobject-$(SNAP)-0.3.0-r149-$(BP)1.tar.gz \
           $(CHANDLERARCHIVES)/zanshin-$(SNAP)-150-$(BP)3.tar.gz \
           $(CHANDLERARCHIVES)/elementtree-$(SNAP)-1.2.6-20050316-$(BP)3.tar.gz \
           $(CHANDLERARCHIVES)/astng-$(SNAP)-0.16.0-$(BP)3.tar.gz \
           $(CHANDLERARCHIVES)/common-$(SNAP)-0.15.0-$(BP)4.tar.gz \
           $(CHANDLERARCHIVES)/pylint-$(SNAP)-0.11.0-$(BP)3.tar.gz \
           $(CHANDLERARCHIVES)/parsedatetime-$(SNAP)-0.6.5-$(BP)1.tar.gz


# readline is only needed for OSX
ifeq ($(OS),Darwin)
    ARCHIVES += $(CHANDLERARCHIVES)/readline-$(SNAP)-5.1-$(BP)2.tar.gz
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

HOST = builds.osafoundation.org
URL  = http://$(HOST)/external/$(PLATFORM)

SETUPTOOLS_EGG  = $(CHANDLERARCHIVES)/setuptools-0.6b3-py2.4.egg
SETUPTOOLS_ABS  = $(SETUPTOOLS_EGG)
SETUPTOOLS_BIN  = $(CHANDLERBIN)/$(SNAP)
SETUPTOOLS_SITE = $(CHANDLERBIN)/$(SITE)
EASYINSTALL_BIN = $(EASYINSTALL)
PLUGIN_ABS      = $(PLUGIN_ARCHIVES)
PYTHON_BIN      = $(CHANDLERBIN)/$(SNAP)/RunPython

#
# The following cygpaths are all done using
# := (or 'simply expanded') to prevent errant
# \ escaping that occurs when = is used
#
ifeq ($(OS),Cygwin)
    PYTHON_BIN      := $(SETUPTOOLS_BIN)/bin/python$(DEBUG_SUFFIX)
    SETUPTOOLS_ABS  := `cygpath -wa $(SETUPTOOLS_EGG)`
    SETUPTOOLS_BIN  := `cygpath -wa $(SETUPTOOLS_BIN)`
    SETUPTOOLS_SITE := `cygpath -wa $(SETUPTOOLS_SITE)`
    EASYINSTALL_BIN := `cygpath -wa $(EASYINSTALL)`
    PLUGIN_ABS      := `cygpath -aw $(PLUGIN_ARCHIVES)`
endif

ARCHIVES_INST = \
    $(addsuffix .inst, \
                $(addprefix $(C_BIN)/$(SNAP)/, \
                            $(notdir $(ARCHIVES))))

PLUGINS_INST = \
    $(addsuffix .inst, \
                $(addprefix $(C_BIN)/$(SNAP)/, \
                            $(notdir $(BUNDLED_PLUGINS))))

PLUGINS_DOWNLOAD = \
                $(addprefix $(PLUGIN_ARCHIVES)/, \
                            $(notdir $(BUNDLED_PLUGINS)))

downloads: $(ARCHIVES) $(PLUGINS_DOWNLOAD)

$(PLUGINS_DOWNLOAD):
	$(CURL) $(PLUGIN_ARCHIVES)/$(notdir $@) $(URL)/$(notdir $@)

$(PLUGINS_INST):
	MACOSX_DEPLOYMENT_TARGET= $(PYTHON_BIN) \
      -c "import sys; sys.path.insert(0,r'$(SETUPTOOLS_ABS)'); from setuptools.command.easy_install import main; main()" \
      --script-dir=$(SETUPTOOLS_BIN) \
      --install-dir=$(SETUPTOOLS_SITE) \
      $(PLUGIN_ABS)/$(notdir $(basename $@))
	touch $@

bundled-plugins: $(PLUGINS_DOWNLOAD) $(PLUGINS_INST)

$(addprefix binaries-, $(BUILD_PLUGINS)):
	cd $(CHANDLERHOME)/projects/$(subst binaries-,,$@); \
    $(PLUGIN_PYTHON) setup.py bdist_egg -d ../../$(CHANDLERARCHIVES)

build-plugins: $(addprefix binaries-, $(BUILD_PLUGINS))

$(ARCHIVES):
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ $(URL)/$(notdir $@)

$(ARCHIVES_INST):
	tar -C $(CHANDLERBIN) -xvzf $(CHANDLERARCHIVES)/$(notdir $(basename $@))
	touch $@

SETUPTOOLS_INST = \
    $(addsuffix .inst, \
                $(addprefix $(CHANDLERBIN)/$(SNAP)/, \
                            $(notdir $(SETUPTOOLS_EGG))))

setuptools: $(SETUPTOOLS_INST)

$(SETUPTOOLS_EGG):
	mkdir -p $(CHANDLERARCHIVES)
	$(CURL) $@ http://$(HOST)/external/$(notdir $@)

$(SETUPTOOLS_INST): $(SETUPTOOLS_EGG)
	MACOSX_DEPLOYMENT_TARGET= $(PYTHON_BIN) \
      -c "import sys; sys.path.insert(0,r'$(SETUPTOOLS_ABS)'); from setuptools.command.easy_install import main; main()" \
      --script-dir=$(SETUPTOOLS_BIN) \
      --install-dir=$(SETUPTOOLS_SITE) \
      $(SETUPTOOLS_ABS)
	touch $@

ifeq ($(OS),Cygwin)
manifest_exe:
	if [ -f "$(CHANDLERBIN)/$(SNAP)/bin/chandler.exe.manifest" ]; \
	then \
	    chmod +x $(CHANDLERBIN)/$(SNAP)/bin/chandler.exe.manifest; \
	fi
else
manifest_exe:
endif

install: $(ARCHIVES) $(ARCHIVES_INST) manifest_exe $(SETUPTOOLS_INST) bundled-plugins

download: $(ARCHIVES) $(SETUPTOOLS_EGG)

# to install individual binaries, for example: make chandlerdb

$(notdir $(shell echo $(ARCHIVES) | sed "s/-$(SNAP)[^ ]*//g")):
	$(MAKE) $(shell echo $(ARCHIVES) | sed "s=.*\($(CHANDLERARCHIVES)/$@-[^ ]*\).*=\1=")
	$(MAKE) $(shell echo $(ARCHIVES_INST) | sed "s=.*\($(CHANDLERBIN)/$(SNAP)/$@-[^ ]*\).*=\1=")


# to install individual eggs, for example: make Chandler_HelloWorldPlugin

$(notdir $(shell echo $(BUNDLED_PLUGINS) | sed $(SED_MODERN) "s/-[0-9]+[^ ]*\.egg//g")):
	$(MAKE) $(PLUGIN_ARCHIVES)/$(shell echo $(BUNDLED_PLUGINS) | sed "s=.*\($@-[^ ]*\).*=\1=")
	$(MAKE) $(CHANDLERBIN)/$(SNAP)/$(shell echo $(PLUGINS_INST) | sed "s=.*\($@-[^ ]*\).*=\1=")


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
	find $(CHANDLERBIN)/release $(STRIP_OP) | xargs chmod +w
	find $(CHANDLERBIN)/release $(STRIP_OP) | xargs strip $(STRIP_OPTIONS)
endif
endif

debug:
	$(MAKE) DEBUG=1 install

purge:
	$(PYTHON_BIN) $(C_HOME)/tools/purge.py $(C_HOME)

check:
	$(PYTHON_BIN) $(C_HOME)/tools/checker.py

lint:
	$(PYTHON_BIN) $(C_HOME)/tools/lint.py

print-%:
	@echo $* = $($*)

tests:
	$(CHANDLERHOME)/tools/do_tests.sh -u

clean:
	rm -rf $(CHANDLERBIN)/$(SNAP)
	rm -rf __repository__
	rm -f chandler.log randpool.dat
	find . -name '*.pyc' | xargs rm -f
	find . -name '*.pyo' | xargs rm -f

realclean: clean
	rm -f $(ARCHIVES)
	rm -rf $(CHANDLERBIN)/debug
	rm -rf $(CHANDLERBIN)/release

