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


import twisted.python.threadable as threadable
import twisted.python.threadpool as threadpool
import chandlerdb.persistence.Repository as Repository

threadable.init()

# Use C{RepositoryThread} instead of the standard python C{Thread}
# in Twisted Thread Pool objects 
threadpool.ThreadPool.threadFactory = Repository.RepositoryThread
