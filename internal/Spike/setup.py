from distutils.core import setup
from distutils.cmd import Command

PACKAGE_NAME = "Spike"
PACKAGE_VERSION = "0.0.0"

SCRIPTS         = []           # No scripts yet
ALL_EXTS        = ['*.txt']    # include text files in installation
PACKAGES        = ['spike', 'spike.tests', 'pim', 'pim.tests']
DEFAULT_SUITE   = 'spike.tests.suite' # default tests to run on 'setup.py test'


class TestCommand(Command):
    """Command to run unit tests after installation"""

    description = "run unit tests after installation"

    user_options = [
        ('suite=','s',"Test suite to run (e.g. 'some_module.test_suite')"),
    ]

    suite = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.suite = self.suite or DEFAULT_SUITE
        self.test_args = [self.suite]

        if self.verbose:
            self.test_args.insert(0,'--verbose')

    def run(self):
        # Install before testing
        self.run_command('install')

        if self.suite:
            cmd = ' '.join(self.test_args)
            if self.dry_run:
                self.announce('skipping "unittest %s" (dry run)' % cmd)
            else:
                self.announce('running "unittest %s"' % cmd)
                import unittest
                unittest.main(None, None, [unittest.__file__]+self.test_args)


setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,

    description="Chandler API Proofs-of-concept",
    author="Phillip J. Eby",
    author_email="pje@telecommunity.com",
    url="http://wiki.osafoundation.org/bin/view/Journal/PhillipEbyNotes",

    extra_path="Spike",     # install to subdirectory of --install-lib path
    cmdclass = {'test':TestCommand},

    packages = PACKAGES,
    package_dir = {'':'src'},   # all packages are found in src/ directory
    package_data = {'': ALL_EXTS},
    scripts = SCRIPTS,
)

