#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from chandlerdb.persistence.DBRepository import DBRepository
from chandlerdb.item.Sets import KindSet

r = DBRepository('data')
r.create()
r = r.view
r.setBackgroundIndexed(True)

r.loadPack('repository/tests/data/packs/cineguide.pack')
k = r.findPath('//CineGuide/KHepburn')
k.movies.addIndex('n', 'numeric')
k.movies.addIndex('t', 'value', attribute='title', ranges=[(0, 1)])
k.movies.addIndex('f', 'string', attributes=('frenchTitle', 'title'),
                  locale='fr_FR')

m1 = r.findPath('//CineGuide/KHepburn').movies.first()
m1.director.itsKind.getAttribute('directed').type = m1.itsKind
k.set = KindSet(m1.itsKind, True)
k.set.addIndex('t', 'value', attribute='title', ranges=[(0, 1)])
m1.director.directed.addIndex('T', 'subindex', superindex=(k, 'set', 't'))

r.check()
r.commit()

r = r.repository
r.close()
