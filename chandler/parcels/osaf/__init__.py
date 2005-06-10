# Initialize gettext.  This makes actual translation attempts futile,
# since we have to hardcode english for tests to work.  This should
# be replaced with a sane alternative when i18n support lands!
#
import os, gettext
os.environ['LANGUAGE'] = 'en'
gettext.install('chandler', 'locale');

# remove namespace clutter
del os, gettext
