# Created: 2005/03/12
# Author: David Elliott

# Usage Example:
#  make -f build/autoconf.mk ACLOCAL=aclocal-1.6

# This is a simple Makefile to update the UNIX build system in such a
# way that doing a cvs diff on its output files should reveal only the
# true changes, not meaningless differences due to slightly different
# autoconf or aclocal m4 files.

# For aclocal: many systems lack some of the .m4 files required by our
# configure script.and some have outdated versions.
# Note that different aclocal versions may reorder some of the macros
# so you may want to hand edit to put them back in the previous order.
# Also, at least my aclocal 1.9 doesn't put acinclude.m4 macros into
# aclocal.m4 but instead does m4_include([acinclude.m4])
# Again, this is easy enough to resolve by a bit of hand tweaking.

# For autoconf: Debian in their infinite wisdom decided to improve upon
# the standard autoconf 2.59 macros. Thus Debian's autoconf generates
# a totally different configure script.  This fixes it to look
# like Debian's (I think).

ACLOCAL=aclocal
AUTOCONF=autoconf
AUTOM4TE=autom4te

# configure depends on everything else so this will build everything.
all: configure

# Run bakefile-gen (which generates everything) whenever files.bkl is newer
# than Makefile.in or autoconf_inc.m4.
# This dep is obviously wrong but probably close enough
autoconf_inc.m4 Makefile.in: build/bakefiles/files.bkl
	cd build/bakefiles
	bakefile_gen -f autoconf

# Run configure whenever configure.in, aclocal.m4 or autoconf_inc.m4 is updated
# Depend on our custom autoconf.m4f
configure: configure.in aclocal.m4 autoconf_inc.m4 build/autoconf_prepend-include/autoconf/autoconf.m4f
	$(AUTOCONF) -B build/autoconf_prepend-include

ACLOCAL_SOURCES = \
  build/aclocal_include/bakefile.m4 \
  build/aclocal_include/cppunit.m4 \
  build/aclocal_include/gst-element-check.m4 \
  build/aclocal_include/gtk-2.0.m4 \
  build/aclocal_include/gtk.m4 \
  build/aclocal_include/pkg.m4 \
  build/aclocal_include/sdl.m4

# Run aclocal whenever acinclude or one of our local m4s is updated.
aclocal.m4: acinclude.m4 $(ACLOCAL_SOURCES)
	$(ACLOCAL) -I build/aclocal_include

AUTOCONF_SOURCES = \
  build/autoconf_prepend-include/autoconf/general.m4 \
  build/autoconf_prepend-include/autoconf/libs.m4 \
  build/autoconf_prepend-include/autoconf/status.m4

# Rule to freeze the m4 so autoconf will actually use it.
# NOTE: VERY important to cd to somewhere there are no .m4 files.
# or at least no aclocal.m4 or else autom4te helpfully picks it up.
build/autoconf_prepend-include/autoconf/autoconf.m4f: $(AUTOCONF_SOURCES)
	cd build/autoconf_prepend-include && \
	$(AUTOM4TE) -B . --language=Autoconf --freeze --output=autoconf/autoconf.m4f

DIST_FILES =\
  $(ACLOCAL_SOURCES) \
  $(AUTOCONF_SOURCES) \
  build/autoconf.mk

# Rule to make a distribution of this stuff
dist:
	tar -c $(DIST_FILES) | bzip2 -c > build/autohacks.tar.bz2
