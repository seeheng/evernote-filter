#
# Script to replace <p> </p> in my notes with line breaks
#
# Notes shared from Android App Malysia News are not properly formatted.
# The HTML paragraph markers remained in the shared note and as a result,
# these notes are not legible.
#
# Before running this sample, you must fill in your Evernote developer token.
#
# To run (Unix):
#   export PYTHONPATH=../../lib; python EDAMTest.py
#

import hashlib
import binascii
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.ttypes as NoteStoreTypes
import evernote.edam.type.ttypes as Types
import evernote.edam.error.ttypes as ErrorTypes

from evernote.api.client import EvernoteClient

import re
from datetime import datetime

# Real applications authenticate with Evernote using OAuth, but for the
# purpose of exploring the API, you can get a developer token that allows
# you to access your own Evernote account. To get a developer token, visit
# https://sandbox.evernote.com/api/DeveloperToken.action
auth_token = "S=s1:U=930b2:E=15f674a64b3:C=1580f993668:P=1cd:A=en-devtoken:V=2:H=e7f5a4a6f9f0c350c27bb114addfaf80"

if auth_token == "your developer token":
    print "Please fill in your developer token"
    print "To get a developer token, visit " \
        "https://sandbox.evernote.com/api/DeveloperToken.action"
    exit(1)

# Initial development is performed on our sandbox server. To use the production
# service, change sandbox=False and replace your
# developer token above with a token from
# https://www.evernote.com/api/DeveloperToken.action
client = EvernoteClient(token=auth_token, sandbox=True)

user_store = client.get_user_store()

version_ok = user_store.checkVersion(
    "Evernote EDAMTest (Python)",
    UserStoreConstants.EDAM_VERSION_MAJOR,
    UserStoreConstants.EDAM_VERSION_MINOR
)
print "Is my Evernote API version up to date? ", str(version_ok)
print ""
if not version_ok:
    exit(1)

    
noteStore = client.get_note_store()

# List all of the notebooks in the user's account, and the #of notes in each notebook
notebooks = noteStore.listNotebooks()
print "Found ", len(notebooks), " notebooks:"

#specify notebook
nf = NoteStoreTypes.NoteFilter()
nf.ascending = True;
nf.inactive = False   #exclude inactive notes
noteCount = noteStore.findNoteCounts(nf,0);  # returns NoteCollectionCounts
nbCount = noteCount.notebookCounts

#specify what type of notemetadata to pull
rSpec = NoteStoreTypes.NotesMetadataResultSpec()
rSpec.includeTitle = True;
rSpec.includeUpdated = True;

# Check date of previous run.  Quit is already done today
# Check number of new notes since last run

# for each of the note, open for edit   
for notebook in notebooks:
    print ""
    print "* ", notebook.name, ": #notes = ", nbCount[notebook.guid]
    
    #get notes 
    nf.notebookGuid = notebook.guid     #specified by notebook's guid
    notesList = noteStore.findNotesMetadata(nf, 0,10, rSpec) #returns NotesMetadataList    
    print "Noteslist startIndex:", notesList.startIndex
    print "Noteslist totalNotes:", notesList.totalNotes
    print "Noteslist updateCount:", notesList.updateCount
    for notedata in notesList.notes:
        print "\r\n"
        titleStr = notedata.title[:63] #limit to 64 chars
        print "NoteTitle:", titleStr
        print "updated:", notedata.updated
        #print "updateSequenceNum:", notedata.updateSequenceNum
        noteContent = noteStore.getNoteContent(notedata.guid)
        #if notedata.title == 'n7':
        #    print noteContent
        if noteContent.find('<?xml version'):  # ensure that the notes are not XML
            updateNeeded = False

            #
            # Update title
            #
            targetStr = "(<br/>)|(<p>)|(&lt;br/&gt;)"
            pat = re.compile(targetStr)
            updateNeeded = pat.search(titleStr)!=None           
            titleStr = pat.sub(" ", titleStr,0) 
            
            #
            #check for incorrect HTML tag            
            #
            targetStr = "&lt;em&gt;"
            pat = re.compile(targetStr)
            updateNeeded = pat.search(noteContent)!=None           
            newNoteContent = pat.sub("<b>", noteContent,0) 
            #print updateNeeded, ":", pat.search(targetStr), ":", targetStr
            
            targetStr = "&lt;/em&gt;"
            pat = re.compile(targetStr)
            updateNeeded = (updateNeeded or (pat.search(noteContent)!=None))
            newNoteContent = pat.sub("</b>", newNoteContent,0)
            #print updateNeeded
            
            targetStr ="(<a/>)|(&lt;a/%gt;)"
            pat = re.compile(targetStr)  #TBD somehow this pattern does not work
            updateNeeded = (updateNeeded or (pat.search(noteContent)!=None))
            newNoteContent = pat.sub(" ", newNoteContent,0)  
            #print updateNeeded
            
            targetStr ="&amp;nbsp;"
            pat = re.compile(targetStr)
            updateNeeded = (updateNeeded or (pat.search(noteContent)!=None))
            newNoteContent = pat.sub(" ", newNoteContent,0)
            #print updateNeeded
            
            targetStr ="&lt;"
            pat = re.compile(targetStr)
            updateNeeded = (updateNeeded or (pat.search(noteContent)!=None))
            newNoteContent = pat.sub("<", newNoteContent,0)
            #print updateNeeded
            
            targetStr ="&gt;"
            pat = re.compile(targetStr)
            updateNeeded = (updateNeeded or (pat.search(noteContent)!=None))
            newNoteContent = pat.sub(">", newNoteContent,0)
            #print updateNeeded
            
            targetStr ="<a/>"
            pat = re.compile(targetStr)
            updateNeeded = (updateNeeded or (pat.search(noteContent)!=None))
            newNoteContent = pat.sub("</a>", newNoteContent,0)  
            print updateNeeded
                    
            #print "***\r\n Found match\r\n", newNoteContent
            if updateNeeded == True :           
                # update note
                try:
                    note = noteStore.getNote(notedata.guid, True, True, True, True)
                    #print "note retrieved ", note.guid
                    #newNote.title = "new"                        
                    note.content = newNoteContent
                    note.title = titleStr
                    nn = noteStore.updateNote(note)
                    #print "note updated, returned note guid", nn.guid
                    #nn = noteStore.createNote(newNote)
                except ErrorTypes.EDAMUserException:
                    print "EDAMUserException", ErrorTypes.EDAMUserException
                    print "before"
                    print noteContent
                    print "after"
                    print newNoteContent
                    nn = noteStore.createNote(note)
                except ErrorTypes.EDAMSystemException:
                    print "EDAMSystemException"
                except ErrorTypes.EDAMNotFoundException:
                    print "EDAMNotFoundException"
                # Save edited note

# Update date of execution
print "timestamp: ", datetime.now()

