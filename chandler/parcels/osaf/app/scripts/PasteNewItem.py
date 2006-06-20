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


# Script to paste the contents of the clipboard into Chandler
#   inspired by Pieter Hartsook 
# For now, we always create a note
note = app_ns().root.NewNote()
# select the body field of the note
app_ns().NotesBlock.widget.SetFocus()
# paste the clipboard there
app_ns().root.Paste()
