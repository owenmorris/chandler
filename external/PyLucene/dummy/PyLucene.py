#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from threading import Thread as PythonThread

VERSION = 'dummy'
LUCENE_VERSION = 'dummy'
DB_VERSION = 'dummy'


class _dummyClass(type):

    def __getattr__(self, name):
        return _dummy()


class _dummy(object):
    __metaclass__ = _dummyClass

    def __init__(self, *args, **kwds):
        pass

    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwds):
        return self

    def __iter__(self):
        return iter(())


Document = _dummy
Field = _dummy
RAMDirectory = _dummy
DbDirectory = _dummy
StandardAnalyzer = _dummy
QueryParser = _dummy
IndexReader = _dummy
IndexWriter = _dummy
IndexSearcher = _dummy
Term = _dummy
TermQuery = _dummy
JavaError = _dummy
MatchAllDocsQuery = _dummy
BooleanQuery = _dummy
BooleanClause = _dummy
