# Script to paste the contents of the clipboard into Chandler
#   inspired by Pieter Hartsook 
# For now, we always create a note
note = app_ns().root.NewNote()
# select the body field of the note
app_ns().NotesBlock.widget.SetFocus()
# paste the clipboard there
app_ns().root.Paste()
