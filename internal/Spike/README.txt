The "Spike" API Prototype
=========================

"Spike" is a common name for a dog, but it's also an XP term meaning a simple,
narrowly-focused prototype to test feasibility and build understanding of a
subject.  The Spike project is a test for the feasibility of various ideas
for creating a simple Python API for developing Chandler data types and
services, as well as for improving the author's understanding of Chandler's
requirements.

The principal goal of Spike is to design an API usable by persons with basic
knowledge of Python, and which is idiomatic for more experienced Python
programmers.  Where appropriate, it will follow established conventions of the
Python language or of popular open-source Python libraries. It will also
translate Chandler's internal terms and concepts into more commonly-used
equivalents.  It's likely that I will make at least some translation mistakes,
so if you're watching and you see one, please let me know.

The first checkin of Spike is a Zero Functionality Release (ZFR, pronounced
"ziffer").  It does absolutely nothing, but it has a ``setup.py``, this
document, and empty packages.  It can be installed, and the tests run.  This is
the basic functionality needed to perform TDD (Test-Driven Development).


Installing and Running Spike
----------------------------

For the ZFR milestone, Spike requires only Python 2.4; you can use stock
Python or the Chandler build.  This will change in future releases as more
requirements are added.

Spike uses a standard Python ``setup.py`` file, so you can build and install
it using the standard ``python setup.py install`` command.  By default,
Spike will be installed to a ``Spike`` subdirectory of Python's
``site-packages`` directory, but you can change this default if you wish.
(See `Alternate Installation`_, below.)

To build and install or upgrade Spike, use::

    python setup.py install

You may use Chandler's ``RunPython`` script to invoke Python, if you like.

Sometimes, an upgrade to Spike may change the package layout and require you
to uninstall the previous version before installing.  To do this, simply
remove the ``Spike`` subdirectory from ``site-packages`` (or from your
alternate location, as described in the next section).  Then, run the
``setup.py install`` command to reinstall.

To run Spike's tests, use::

    python setup.py test

This will run Spike's tests, after upgrading the existing installation if
necessary.  Note that the installation location must be on the ``PYTHONPATH``
when using this command.  If you installed to the default location (Python's
``site-packages``), this is taken care of automatically, but if you are using
a custom location you must add it to your ``PYTHONPATH`` environment variable.
(More below.)

The default format for test output is a bit verbose, so as the number of tests
grows, you may find the "quiet" version more useful::

    python setup.py -q test

This will only print a dot for each test run, or an "E" or "F" if a test
has an error or failure.  At the end of the run, a report with detailed error
information will be produced.

Note, by the way, that Spike code in CVS should *never* have test failures or
errors.  If you encounter such an error, please report it to me at once.  It's
not a "work in progress" error, because I will only be checking in code to
Spike if the changes pass all tests in my development environment.


Alternate Installation
----------------------

If you don't wish to install Spike to your Python ``site-packages`` directory,
you can change the location by creating a ``setup.cfg`` file to control where
installation goes.  The file should be placed in your Spike checkout's main
directory (i.e. the directory containing this README), and its contents should
look something like this::

    [install]
    install_lib = /path/where/you/want/it/installed

Then, when you run setup.py, Spike will be installed to the named directory,
rather than Python's ``site-packages`` directory.  However, Spike's actual
installation directory must be on your ``PYTHONPATH`` when you run Spike's
tests.

For example, if you set the ``install_lib`` in ``setup.cfg`` to ``/foo/bar``,
then ``/foo/bar/Spike`` must be listed in ``PYTHONPATH``.  Also, if you need
to uninstall Spike before upgrading it, you can do so by removing the
``/foo/bar/Spike`` directory.


Documentation
-------------

Spike's documentation will mostly consist of tutorials containing doctest
examples.  Thus, the examples will always be guaranteed to work, because they
are tested as part of Spike's testing process.

Documentation (like this README) will be written using reStructuredText, a
Wiki-like plain text markup format supported by various Python tools including
epydoc and several wiki and blogging programs.  The Python docutils package
(http://docutils.sf.net/) includes tools to produce HTML, LaTeX, PDF, and other
output formats from reStructuredText input.  The reStructuredText format
also "understands" doctest example blocks, which is useful because Spike's
documentation will contain lots of such examples.

As of the current version, however, the documentation is only provided in its
source text form, not in any processed form.  In a later release, some
documentation processing may become automated via ``setup.py``, but that will
add a dependency on the Docutils package, and I'd prefer the Zero Functionality
release to be as close to a Zero Dependency release as possible.  :)

