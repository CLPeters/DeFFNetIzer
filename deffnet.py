#!/usr/bin/env python2.4
#    deffnet - A program to extract fanfics from fanfiction.net
#    Copyright (C) 2005 by Jonathan Rosebaugh
#    Some 'import'ed modules may have a different copyright. Examine them
#    for details.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of version 2 of the GNU General Public License as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import BeautifulSoup
import openanything
import re
import os
import sys, traceback, cStringIO
import codecs
import socket, errno
from urllib2 import urlopen
from platform import platform
from Tkinter import *
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import configs
import dircopy
import time
import rClickclass as rC

# This should deal with timeouts.
socket.setdefaulttimeout(10) # Times out after ten seconds now

# Build Date: 11/15/2013
deffnet_version = "2456611.9375"
deffnet_version_name = "FFNet Only"

# Insert Deep Magic here:
fixer = re.compile(r"(<html>.*)<[x|h]tml[^>]*>.*<body[^>]*>(.*)</body>.*</span>",re.I|re.S)
def fixhtml(source):
    """Some html at ff.net is REALLY broken, and will cause Beautiful Soup
    to shrug its shoulders and give up. This should deal with most of it."""
   
    return fixer.sub(r'\1\2',source)    


class ExceptionBox(tkSimpleDialog.Dialog):
    def __init__(self, parent, title = None, exceptiontext = ""):
        self.exceptiontext = exceptiontext
        tkSimpleDialog.Dialog.__init__(self, parent, title)
       
    def body(self, master):
        label = Label(master, text = "Please submit a support ticket ( http://www.clpnetworks.com/contact/ ) with the information below:")
        label.grid(row=0)
       
        frame = Frame(master)
        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill=Y)
       
        textbox = Text(frame, yscrollcommand=scrollbar.set)
        textbox.insert(END, self.exceptiontext)
        textbox.pack(side=LEFT, fill=BOTH)
       
        scrollbar.config(command=textbox.yview)
        frame.grid(row=1)
        return textbox
#        button = Button(master, text = "Close")
#        button.grid(row=2)

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
       
        box = Frame(self)
   
        w = Button(box, text="Close", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)
   
        self.bind("&lt;Return>", self.cancel)
        self.bind("&lt;Escape>", self.cancel)
   
        box.pack()

class Pref(tkSimpleDialog.Dialog):
    def __init__(self, parent, title = None, appobj = None):
        self.appobj = appobj
        tkSimpleDialog.Dialog.__init__(self, parent, title)

       
    def body(self, master):
        self.location = self.appobj.location
        self.secondary = IntVar()
        self.secondary.set(self.appobj.secondary.get())
        self.checkupdate = IntVar()
        self.checkupdate.set(self.appobj.checkupdate.get())
       
        self.templatepath = self.appobj.templatepath
        self.useragent = self.appobj.useragent

        self.labels = {}
        self.entryboxes = {}
        self.buttons = {}
        self.misc = {}

        self.labels['Location'] = Label(master, text="Location to Save:")
        self.labels['Location'].grid(row=0, column=0, sticky=E)
        self.entryboxes['Location'] = Entry(master)
        self.entryboxes['Location'].grid(row = 0, column=1, sticky=W)
        self.entryboxes['Location'].delete(0,END)
        self.entryboxes['Location'].insert(0, self.location)
        self.buttons['Location'] = Button(master, text="Browse", command=self.getlocation)
        self.buttons['Location'].grid(row=0, column=2)
        self.labels['Template'] = Label(master, text="Template to Use:")
        self.labels['Template'].grid(row=1, column=0, sticky=E)
        self.entryboxes['Template'] = Entry(master)
        self.entryboxes['Template'].grid(row = 1, column=1, sticky=W)
        self.entryboxes['Template'].delete(0,END)
        self.entryboxes['Template'].insert(0, self.templatepath)
        self.buttons['Template'] = Button(master, text="Browse", command=self.gettemplate)
        self.buttons['Template'].grid(row=1, column=2)
        self.misc['Secondary'] = Checkbutton(master, text = "Enable Secondary Chapter Algorithm",  variable=self.secondary)
        self.misc['Secondary'].grid(row=2, columnspan=3)

        #self.labels['Agent'] = Label(master, text="User Agent:")
        #self.labels['Agent'].grid(row=3, column=0, sticky=E)
        #self.entryboxes['Agent'] = Entry(master)
        #self.entryboxes['Agent'].grid(row=3, column=1, sticky=W, columnspan=2)
        #self.entryboxes['Agent'].delete(0,END)
        #self.entryboxes['Agent'].insert(0, self.useragent)
        self.misc['Checkupdate'] = Checkbutton(master, text = "Check for updates on startup",  variable=self.checkupdate)
        self.misc['Checkupdate'].grid(row=4, columnspan=3)
       
    def apply(self):
        self.appobj.location = self.location
        self.appobj.templatepath = self.templatepath
        self.appobj.secondary.set(self.secondary.get())
        self.appobj.checkupdate.set(self.checkupdate.get())
        self.appobj.useragent = str(self.useragent)

    def getlocation(self):
        if os.path.exists(self.location):
            l = tkFileDialog.askdirectory(initialdir=self.location, mustexist=True)
        else:
            l = tkFileDialog.askdirectory(mustexist=True)
        if os.path.exists(l):
            self.location = l
        self.entryboxes['Location'].delete(0,END)
        self.entryboxes['Location'].insert(0, self.location)
       
    def gettemplate(self):
        if os.path.exists(self.templatepath):
            l = tkFileDialog.askdirectory(initialdir=self.templatepath, mustexist=True)
        else:
            l = tkFileDialog.askdirectory(mustexist=True)
        if os.path.exists(l):
            self.templatepath = l
        self.entryboxes['Template'].delete(0,END)
        self.entryboxes['Template'].insert(0, self.templatepath)



class App:

    def __init__(self, master):
        self.master = master
        self.master.title("The De-FFNet-izer")

        self.configobj = configs.TheConfig()

        self.version = deffnet_version
        self.version_name = deffnet_version_name

        self.frames = {}
        self.labels = {}
        self.entryboxes = {}
        self.buttons = {}
        self.misc = {}
       
        self.menus = {}
       
        self.forceencoding = ''
        self.tryencoding = 'utf-8'
        self.completed = IntVar()
        self.oneshot = IntVar()
        self.secondary = IntVar()
        self.checkupdate = IntVar()
        self.completed.set(0)
        self.oneshot.set(0)
        self.secondary.set(0)
        self.checkupdate.set(0)
        self.chaptercheck = "completed"
       
        self.loadopts()

        self.menus['main'] = Menu(self.master)
        self.menus['file'] = Menu(self.menus['main'])
        self.menus['main'].add_cascade(label="File", menu=self.menus['file'])
        self.menus['file'].add_command(label="Set Preferences", command=self.displaypref)
        self.menus['file'].add_separator()
        self.menus['file'].add_command(label="About", command=self.displayabout)
        self.menus['file'].add_separator()
        self.menus['file'].add_command(label="Quit", command=self.quitit)
       
        self.master.config(menu=self.menus['main'])

        self.master.protocol("WM_DELETE_WINDOW", self.quitit)        

        self.frames['Story'] = Frame(self.master, borderwidth=1, relief=RIDGE)
        self.frames['Story'].grid(row=0, sticky=E+W)
        self.frames['Chapters'] = Frame(self.master, borderwidth=1, relief=RIDGE)
        self.frames['Chapters'].grid(row=1, sticky=E+W)
        self.frames['Directory'] = Frame(self.master, borderwidth=1, relief=RIDGE)
        self.frames['Directory'].grid(row=2, sticky=E+W)
        self.frames['Advanced'] = Frame(self.master, borderwidth=1, relief=RIDGE)
        self.frames['Advanced'].grid(row=3, sticky=E+W)
        self.frames['Status'] = Frame(self.master, borderwidth=1, relief=RIDGE)
        self.frames['Status'].grid(row=4, sticky=E+W)

        self.labels['Story ID'] = Label(self.frames['Story'], text="Please enter Story ID")
        self.labels['Story ID'].grid(row=0, column=0, sticky=W)
       
        self.entryboxes['Story ID'] = Entry(self.frames['Story'])
        self.entryboxes['Story ID'].grid(row=1, column=0, sticky=W)
       
        self.buttons['Story ID'] = Button(self.frames['Story'], text="Fetch", command=self.handlestory)
        self.buttons['Story ID'].grid(row=2, column=0)
       
        self.labels['TitleLabel'] = Label(self.frames['Story'], text="Title: ")
        self.labels['TitleLabel'].grid(row=0, column=1, sticky=E)

        self.labels['AuthorLabel'] = Label(self.frames['Story'], text="Author: ")
        self.labels['AuthorLabel'].grid(row=1, column=1, sticky=E)

        self.labels['NumChapsLabel'] = Label(self.frames['Story'], text="# of Chapters: ")
        self.labels['NumChapsLabel'].grid(row=2, column=1, sticky=E)

        self.labels['Title'] = Label(self.frames['Story'], text="")
        self.labels['Title'].grid(row=0, column=2, sticky=W)

        self.labels['Author'] = Label(self.frames['Story'], text="")
        self.labels['Author'].grid(row=1, column=2, sticky=W)

        self.labels['NumChaps'] = Label(self.frames['Story'], text="")
        self.labels['NumChaps'].grid(row=2, column=2, sticky=W)
       
       
        self.labels['Chapters'] = Label(self.frames['Chapters'], text="Chapters:")
        self.labels['Chapters'].grid(row=0, column=0, sticky=E)
       
        self.entryboxes['Chapters'] = Entry(self.frames['Chapters'], state=DISABLED)
        self.entryboxes['Chapters'].grid(row=0, column=1, sticky=W)
       
        self.buttons['Chapters'] = Button(self.frames['Chapters'], text="Fetch", state=DISABLED, command=self.handlechapters)
        self.buttons['Chapters'].grid(row=0, column=2)
       

        self.labels['Directory'] = Label(self.frames['Directory'], text="Directory Name:")
        self.labels['Directory'].grid(row=1, column=0, sticky=E)
        self.entryboxes['Directory'] = Entry(self.frames['Directory'], state=DISABLED)
        self.entryboxes['Directory'].grid(row = 1, column=1, sticky=W)
        self.buttons['Directory'] = Button(self.frames['Directory'], text="Save", state=DISABLED, command=self.savefiles)
        self.buttons['Directory'].grid(row=1, column=2)
       
       
        self.labels['Advanced'] = Label(self.frames['Advanced'], text="Advanced Options - Please read documentation first")
        self.labels['Advanced'].grid(row=0, column=0, columnspan=2)

        self.misc['Completed'] = Checkbutton(self.frames['Advanced'], text = "Completed", state=DISABLED, variable=self.completed)
        self.misc['Completed'].grid(row=1, column=0, sticky=W)
       
        self.labels['VersionLabel'] = Label(self.frames['Advanced'], text="Version:")
        self.labels['VersionLabel'].grid(row=0, column=2, sticky=E)
       
        self.labels['Version'] = Label(self.frames['Advanced'], text=self.version)
        self.labels['Version'].grid(row=1, column=2, sticky=E)

        self.misc['Oneshot'] = Checkbutton(self.frames['Advanced'], text = "Oneshot", state=DISABLED, variable=self.oneshot)
       

        self.labels['Encoding'] = Label(self.frames['Advanced'], text = "Override Encoding:")
        self.labels['Encoding'].grid(row=2, column=0, sticky=W)
       
        self.entryboxes['Encoding'] = Entry(self.frames['Advanced'])
        self.entryboxes['Encoding'].grid(row=2, column=1, sticky=W)

        self.labels['Status'] = Label(self.frames['Status'], text="Status: Ready")
        self.deffg = self.labels['Status']['fg']
        self.defbg = self.labels['Status']['bg']

        self.labels['Status'].pack(fill=BOTH, side=LEFT)
       
        self.story = 0
        self.chapterstring = ""
#        self.checkupdates()
       
        self.checkprefsset()


    def checkprefsset(self):
        if self.location is "" or self.templatepath is "":
            tkMessageBox.showinfo("The De-FFNet-izer", "Please set your preferences before using this program. You can find the 'Set Preferences' item in the 'File' menu.")
       
    def checkupdates(self):
        if self.checkupdate.get() is 0:
            return
        myagent = "deffnet %s %s" % (self.version, platform())
        try:
            latest = self.fetch("http://www.deffnetizer.com/version-ffnonly.txt", myagent).strip()
        except:
            tkMessageBox.showinfo("The De-FFNet-izer","The De-FFNet-izer was unable to check for updates. If this is a recurring problem, you may wish to turn off the update checking in the Preferences.")
        else:
            if float(latest) > float(self.version):
                tkMessageBox.showinfo("The De-FFNet-izer","You are currently running version %s, but version %s is available from http://www.deffnetizer.com" % (self.version, latest))

    def displayabout(self):
        tkMessageBox.showinfo("The De-FFNet-izer","""The De-FFNet-izer is copyright 2005 by Jonathan Rosebaugh.
Official Website: http://www.deffnetizer.com

Originally Created By: Jonathan Rosebaugh - http://www.inklesspen.com/
Maintained By: Chad Peterson (7/4/2007 - Present)

This program is free software; you can redistribute it and/or modify it under the terms of version 2 of the GNU General Public License as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.""")

    def displaypref(self):
        p = Pref(self.master, "Preferences", self)

    def handlestory(self):
        try:
            # Unicode fun stuff
            self.codecs = ['utf-8', 'latin-1', 'niceutf-8']
            try:
                c = self.entryboxes['Encoding'].get()
                codecs.getencoder(c)
                self.codecs.insert(0,c)
            except LookupError:
                pass
   
            try:
                # Strip out all non-digit characters.
                self.story = int(re.sub(r'\D',"",self.entryboxes['Story ID'].get()))
            except ValueError:
                self.setstatus("Invalid Story ID", True)
                return



   
            self.setstatus("Retrieving story info")
            self.soups = {}
            source = self.retrieveChapter(1)
   
            self.soups[1] = self.makeSoup(source) # Fetch down the first chapter to extract metadata
            self.numchaps, self.title, self.author = self.extractStoryInfo(self.soups[1])
   
            self.labels['Title']['text'] = self.title
            self.labels['Author']['text'] = self.author
            self.labels['NumChaps']['text'] = self.numchaps
            self.entryboxes['Chapters']['state'] = NORMAL
            self.buttons['Chapters']['state'] = NORMAL
   
   
            self.entryboxes['Chapters'].delete(0,END)
            self.entryboxes['Directory'].delete(0,END)
            self.entryboxes['Directory']['state'] = DISABLED
            self.buttons['Directory']['state'] = DISABLED
                   
            self.completedshow()
            self.completedenable(False)        
            self.completedchecked(False)
            self.oneshotchecked(False)
   
       
            self.setstatus("Ready")
        except:
            builder = cStringIO.StringIO()
            builder.write("Platform: %s\nStory: %d\n\n" % (platform(), self.story))
           
            traceback.print_exc(file=builder)
            e = ExceptionBox(root, "Exception", builder.getvalue())

   
    def handlechapters(self):
        try:
            # parse and retrieve chapters.
            self.chapterstring = self.entryboxes['Chapters'].get()
            if self.chapterstring == "":
                self.chapterstring = "*"
            self.chapters = self.parseChapters(self.chapterstring.replace(" ",""), self.numchaps)
            for chap in self.chapters:
                if not self.soups.has_key(chap):
                    self.setstatus("Retrieving chapter %d." % chap)
                    try:
                        source = self.retrieveChapter(chap)
                    except Exception:
                        self.setstatus("Unable to retrieve chapter %d." % chap, True)
                    else:
                        self.soups[chap] = self.makeSoup(source)
   
            self.entryboxes['Directory']['state'] = NORMAL
            self.entryboxes['Directory'].delete(0,END)
            self.entryboxes['Directory'].insert(0,self.makedirname(self.title))
            self.buttons['Directory']['state'] = NORMAL
   
            # Setup completed / oneshot
   
            if self.soups.has_key(self.numchaps) and self.numchaps > 1:
                self.completedshow()
                self.completedenable(True)
            elif self.numchaps > 1 and not self.soups.has_key(self.numchaps):
                self.completedshow()
                self.completedenable(False)
            elif self.numchaps == 1:
                self.oneshotshow()
                self.oneshotenable(True)
   
   
            self.completedchecked(False)
            self.oneshotchecked(False)
            # check box if necessary
           
            if "Complete" in str(self.soups[1].first('a', {'href':'http://www.fictionratings.com/'}).parent.contents):
                if self.numchaps == 1:
                    self.oneshotchecked(True)
                elif self.soups.has_key(self.numchaps) and self.numchaps > 1:
                    self.completedchecked(True)
   
    #        if self.soups.has_key(self.numchaps):
    #            self.misc['Completed']['state'] = NORMAL
    #            if self.numchaps == 1:
    #                self.misc['Completed'].grid_forget()
    #                self.misc['Oneshot'].grid(row=1, column=0, sticky=W)
    #                self.misc['Oneshot']['state'] = NORMAL
    #        self.misc['Oneshot']['state'] = NORMAL
            self.setstatus("Ready")
        except:
            builder = cStringIO.StringIO()
            builder.write("Platform: %s\nStory: %d\nChapters: %s\n\n" % (platform(), self.story, self.chapterstring))
           
            traceback.print_exc(file=builder)
            e = ExceptionBox(root, "Exception", builder.getvalue())


    def completedshow(self):
        if self.chaptercheck == "completed":
            return
        self.misc['Oneshot'].grid_forget()
        self.misc['Completed'].grid(row=1, column=0, sticky=W)
        self.chaptercheck = "oneshot"

   
    def completedenable(self,tf):
        if tf:
            self.misc['Completed']['state'] = NORMAL
        else:
            self.misc['Completed']['state'] = DISABLED
       
    def completedchecked(self,tf):
        if tf:
            self.completed.set(1)
        else:
            self.completed.set(0)
   
    def oneshotshow(self):
        if self.chaptercheck == "oneshot":
            return
        self.misc['Completed'].grid_forget()
        self.misc['Oneshot'].grid(row=1, column=0, sticky=W)
        self.chaptercheck = "oneshot"
   
    def oneshotenable(self,tf):
        if tf:
            self.misc['Oneshot']['state'] = NORMAL
        else:
            self.misc['Oneshot']['state'] = DISABLED
   
    def oneshotchecked(self,tf):
        if tf:
            self.oneshot.set(1)
        else:
            self.oneshot.set(0)

    def makedirname(self, title):
        title = title.encode('ascii', 'replace')
        storyid = self.story
        author = self.author
        try:
            dirname = self.dirtmpl % ({'title':title, 'storyid':storyid, 'author':author})
        except:
            dirname = title
            
        dirname = dirname.replace(':','-').replace('?','-')
        dirname = re.sub(r'([\:*?"<>|]|\.\.\.)', '-', dirname)
        
        return dirname
       
    def loadopts(self):
        self.location = self.configobj.get('savepath', '')
        self.templatepath = self.configobj.get('templatepath', '')
        self.secondary.set(int(self.configobj.get('secondary',1)))
        
        #FF.Net started to filter by useragent so this was changed to be a real browser...
        #self.useragent = self.configobj.get('useragent', "Python-urllib/2.4")
        self.useragent = self.configobj.get('useragent', "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:23.0) Gecko/20131011 Firefox/23.0")
        self.checkupdate.set(int(self.configobj.get('checkupdate',1)))
        self.dirtmpl = self.configobj.get('dirtmpl', '%(title)s')
        self.basezeroes = int(self.configobj.get('basezeroes', 5))
       
    def saveopts(self):
        if os.path.exists(self.location):
            self.configobj.set('savepath', self.location)
        if os.path.exists(self.templatepath):
            self.configobj.set('templatepath', self.templatepath)
        self.configobj.set('secondary', str(self.secondary.get()))
        self.configobj.set('checkupdate', str(self.checkupdate.get()))
        self.configobj.set('useragent', self.useragent)
        self.configobj.set('dirtmpl', self.dirtmpl)
        self.configobj.set('basezeroes', self.basezeroes)

    def savefiles(self):
        workdir = ""
        try:
            # Make sure template path exists. This isn't normally going to be
            # a problem
            if not os.path.exists(os.path.join(self.templatepath,'normal.html')):
                self.vileerror("The templates cannot be found.")
                return
   
   
            d = self.entryboxes['Directory'].get()
            workdir = os.path.join(self.location, d)
            try:
                os.mkdir(workdir)
            except OSError, (errnum, strerror):
                if errnum == errno.EEXIST:
                    if not tkMessageBox.askyesno("Directory exists", "The specified directory already exists. If you continue, files may be overwritten if they have the same filenames as the chapters you requested. Do you wish to continue?"):
                        self.setstatus("Directory already exists.", True)
                        return
                elif errnum == errno.ENOENT or errnum==errno.EINVAL:
                    self.setstatus("Illegal directory name specified. Please check for illegal characters.", True)
                    return
                else:
                    tkMessageBox.showerror("Unexpected OS Error", "The error %s was detected. Please report this as a bug. First, however, please be sure you aren't using illegal characters in your directory name, and that your hard drive isn't full, and other things that could plausibly have gone wrong." % errno.errorcode[errnum])
                    return
   
            self.templates = {}
            l = os.listdir(self.templatepath)
            l.remove('normal.html')
            self.templates['normal'] = open(os.path.join(self.templatepath,'normal.html'), 'rb').read()
            if os.path.exists(os.path.join(self.templatepath,'first.html')):
                l.remove('first.html')
                self.templates['first'] = open(os.path.join(self.templatepath,'first.html'), 'rb').read()
            if os.path.exists(os.path.join(self.templatepath,'oneshot.html')):
                l.remove('oneshot.html')
                self.templates['oneshot'] = open(os.path.join(self.templatepath,'oneshot.html'), 'rb').read()
            if os.path.exists(os.path.join(self.templatepath,'last.html')):
                l.remove('last.html')
                self.templates['last'] = open(os.path.join(self.templatepath,'last.html'), 'rb').read()
            if os.path.exists(os.path.join(self.templatepath,'index.html')):
                l.remove('index.html')
                self.templates['index'] = open(os.path.join(self.templatepath,'index.html'), 'rb').read()
                if 'index.header' in l:
                    l.remove('index.header')
                if 'index.chapter' in l:
                    l.remove('index.chapter')
                if 'index.footer' in l:
                    l.remove('index.footer')
            else:
                if os.path.exists(os.path.join(self.templatepath,'index.header')) and os.path.exists(os.path.join(self.templatepath,'index.chapter')) and os.path.exists(os.path.join(self.templatepath,'index.footer')):
                    l.remove('index.header')
                    self.templates['index.header'] = open(os.path.join(self.templatepath,'index.header'), 'rb').read()
                    l.remove('index.chapter')
                    self.templates['index.chapter'] = open(os.path.join(self.templatepath,'index.chapter'), 'rb').read()
                    l.remove('index.footer')
                    self.templates['index.footer'] = open(os.path.join(self.templatepath,'index.footer'), 'rb').read()
           
   
            for f in l:
                if os.path.isfile(os.path.join(self.templatepath, f)):
                    open(os.path.join(workdir, f), 'wb').write(open(os.path.join(self.templatepath, f), 'rb').read())
                elif os.path.isdir(os.path.join(self.templatepath, f)):
                    dircopy.copy_dir(os.path.join(self.templatepath, f), workdir)
                 
   
            # Get all the chapter names:
            self.chapnames = {}
            for chapnum in range(1, self.numchaps+1):
                self.chapnames[chapnum] = self.extractChapterTitle(chapnum)
       
   
            self.setstatus("Writing index file.")
            fname = os.path.join(workdir, 'index.html')
            f = codecs.open(fname,'w', 'utf-8')
            f.write(self.genIndex(self.completed.get() or self.oneshot.get(), self.templates))
            f.close()
   
            for chap in self.chapters:
                self.setstatus("Writing chapter %d." % chap)
                fname = os.path.join(workdir,'%04d.html' % chap)
                f = codecs.open(fname,'w', 'utf-8')
                text = self.extractChapterText(self.soups[chap])
                f.write(self.genPage(text, chap, self.completed.get() or self.oneshot.get(), self.templates))
                f.close()
   
            self.setstatus("Done")
#            raise Exception

        except:
            builder = cStringIO.StringIO()
            builder.write("Platform: %s\nStory: %d\nChapters: %s\nSave Directory: %s\n\n" % (platform(), self.story, self.chapterstring, workdir))
           
            traceback.print_exc(file=builder)
            e = ExceptionBox(root, "Exception", builder.getvalue())

       
    def decodeit(self, text):
        mycodecs = list(self.codecs)
        successful = False # Recursion probably isn't the answer here
        while not successful:
            try:
                curcode = mycodecs[0]
                if curcode == "niceutf-8":
                    out = unicode(text, 'utf-8', 'replace')
                else:
                    out = unicode(text, curcode)
                successful = True
            except UnicodeDecodeError:
                mycodecs.pop(0)
        return out

    def quitit(self):
        self.saveopts()
        self.configobj.write()
        self.master.quit()

    def setstatus(self, text, error=False):
        if error is True:
            self.labels['Status']['fg'] = 'red'
            self.labels['Status']['bg'] = self.defbg
            self.labels['Status']['text'] = "Error: " + str(text)
        else:
            self.labels['Status']['fg'] = self.deffg
            self.labels['Status']['bg'] = self.defbg
            self.labels['Status']['text'] = "Status: " + str(text)
        self.labels['Status'].update_idletasks()
       

    def vileerror(self,text):
        tkMessageBox.showerror("An error has occured", text)
    
    #FF.Net started to filter by useragent so this was changed to be a real browser...
    #def fetch(self, url, agent="Python-urllib/2.4"):
    def fetch(self, url, agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:23.0) Gecko/20131011 Firefox/23.0"):
        """Fetch down a url using openanything. This function is wrapped
        for simplicity."""
        result =  openanything.fetch(url, None, None, agent)
        if not result['status'] == 200:
            raise StandardError('Tried to fetch ' + url + ' and got ' + str(result['status']))
        return result['data']

    def retrieveChapter(self, chapnum, czeros=None, gzip=True):
        """This will put together a url and fetch the chapter, hopefully
        dealing with any errors."""
        if not czeros:
            czeros = self.basezeroes
        try:
            chap = "0"*czeros + str(chapnum)         
            url = "https://www.fanfiction.net/s/%(story)d/%(chap)s/" % {'story': self.story, 'chap': chap}
            if gzip==True:
                strsource = self.fetch(url)	
				#Change this if you want a shorter or longer delay
                time.sleep(3.0)
            else:
                strsource = urlopen(url).read()
				#Change this if you want a shorter or longer delay
				#time.sleep(3.0)
				
            source = self.decodeit(strsource)
            if not "<html>" in source:
                raise Exception
        except IOError:
            source = self.retrieveChapter(chapnum, czeros=czeros, gzip=False)
        except:
            if czeros < self.basezeroes+15:
                source = self.retrieveChapter(chapnum, czeros = czeros + 1, gzip=gzip)
            else:
                self.setstatus("Unable to retrieve chapter", True)
                self.vileerror("Unable to retrieve story %d, chapter %d. I tried %d times. Please check that https://www.fanfiction.net/s/%d/%d/ is a working url." % (self.story, chapnum-self.basezeroes, czeros, self.story, chapnum))
                raise Exception
#                raise Exception, "Infinite Loop on %d - %d. %d times. Please check that https://www.fanfiction.net/s/%d/%d/ is a working url." % (self.story, chapnum, czeros, self.story, chapnum)
        return source

    def makeSoup(self, source):
        return BeautifulSoup.BeautifulSoup(fixhtml(source))

    def extractChapterText(self, soup):
        text = unicode(soup.first('div', {'id':'storytext','class':'storytext xcontrast_txt nocopy'}))
        textStart = text.find('<div')
        textEnd = - len('</div>')
        text = text[textStart:textEnd]

        if self.secondary.get()==0 or len(text)>0:
            return text
        else:
            while soup.script is not BeautifulSoup.Null:
                a = unicode(soup.script)
                resource = unicode(soup)
                resource = resource.replace(a,"")
                soup = self.makeSoup(resource)
            starttext = unicode(soup.first('div', {'id':'storytext','class':'storytext'}).findNext('div', {'id':'storytext','class':'storytext'}))
            endtext = unicode(soup.first('div', {'style':'height:5px'}))
            startpos = resource.find(starttext)+len(starttext)
            endpos = resource.find(endtext)
            return unicode(resource[startpos:endpos], "utf-8")

    def extractChapterTitle(self, curchap):
        if self.numchaps == 1:
            if self.oneshot.get() == 1:
                return self.title
            else:
                return "Chapter 1"
        chapname = self.soups[1].first('select', {'title':'Chapter Navigation'}).contents[curchap-1].string
        stripstring = u"%d. " % curchap
        chapname = chapname.replace(stripstring, '')
        return chapname

    def extractStoryInfo(self, soup):
        numchaps = len(soup.first('select', {'title':'Chapter Navigation'}).contents)
        if numchaps == 0:
            numchaps = 1
        title = soup.first('b', {'class':'xcontrast_txt'}).string     
        author = soup.first('a',{'href':re.compile(r'/u/\d+/')}).string
        return numchaps, title, author

    def parseChapters(self, chapters, numchaps):
        if chapters == "*":
            chapters = range(1,numchaps+1)
        else:
            l = []
            bits = chapters.split(",")
            for x in bits:
                if "-" in x:
                    if x.count("-") > 1:
                        raise Exception, "Too many hyphens in " + chapters
                    r = x.split("-")
                    l.extend(range(int(r[0]),int(r[1])+1))
                else:
                    l.extend([int(x)])
            chapters = [x for x in l if x <= numchaps]
           
        return chapters
       
    def genIndex(self, completed=0, templates=None):
        chosen = ""
        if templates.has_key('index'):
            t = templates['index']
            templates['index.header'] = t[:t.find('<!-- Chapter loop start -->')+27] + '\n'
            templates['index.chapter'] = t[t.find('<!-- Chapter loop start -->')+27:t.find('<!-- Chapter loop end -->')].strip() + '\n'
            templates['index.footer'] = t[t.find('<!-- Chapter loop end -->'):]
            del templates['index']
            chosen = "index"
   
        if templates.has_key('index.header') and templates.has_key('index.chapter') and templates.has_key('index.footer'):
       
            try:
                if not chosen=="index":
                    chosen="index.header"
                page = templates['index.header'] % {'title':self.title, 'author':self.author, 'numchaps':self.numchaps, 'storyid':self.story}
           
                if not chosen=="index":
                    chosen="index.chapter"
                for x in range(1,self.numchaps+1):
                    chapfile = "%04d.html" % x
                    page = page + templates['index.chapter'] % {'chapfile':chapfile, 'chapnum':x, 'title':self.title, 'author':self.author, 'numchaps':self.numchaps, 'storyid':self.story, 'chapname':self.chapnames[x]}
               
                if not chosen=="index":
                    chosen="index.footer"
                page = page + templates['index.footer'] % {'title':self.title, 'author':self.author, 'numchaps':self.numchaps, 'storyid':self.story}
                return page

            except KeyError, inst:
                key = inst.args[0]
                self.vileerror('KeyError: Invalid key "%s" in template %s' % (key, chosen))
                return "Error reported!"
            except ValueError:
                self.vileerror('ValueError in template %s' % chosen)
                return "Error reported!"
            except TypeError:
                self.vileerror('TypeError in template %s' % chosen)
                return "Error reported!"
            except:
                self.vileerror('Unidentified exception while processing template %s. Please report this.' % chosen)
                return "Error reported!"
   
        page = """<?xml version="1.0" encoding="iso-8859-1"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
    <title>%(title)s</title>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
    </head>
    <body>
    <p>%(title)s - %(author)s</p>
    <p>""" % {'title':self.title, 'author':self.author}
   
        for x in range(1,self.numchaps):
           page = page + '<a href="%(chap)04d.html">Chapter %(chap)d</a><br />' % {'chap': x}
       
        page = page + """<a href="%(chap)04d.html">Chapter %(chap)d</a></p>
    </body>
    </html>""" % {'chap': self.numchaps}
        return page
       
       
    def genPage(self, data, chapnum, completed=0, templates=None):
        if completed==1 and self.numchaps==1 and templates.has_key('oneshot'):
            t = templates['oneshot']
            chosen = 'oneshot'
        elif chapnum == 1 and templates.has_key('first'):
            t = templates['first']
            chosen = 'first'
        elif chapnum==self.numchaps and completed==1 and templates.has_key('last'):
            t = templates['last']
            chosen = 'last'
        else:
            t = templates['normal']
            chosen = 'normal'
        prev = "%04d.html" % (chapnum-1)
        next = "%04d.html" % (chapnum+1)
        try:
            return t % {'title': self.title, 'author': self.author, 'chapnum': chapnum, 'prev': prev, 'next': next, 'body': data, 'numchaps': self.numchaps, 'storyid':self.story, 'chapname':self.chapnames[chapnum]}
        except KeyError, inst:
            key = inst.args[0]
            self.vileerror('KeyError: Invalid key "%s" in template %s' % (key, chosen))
            return "Error reported!"
        except ValueError:
            self.vileerror('ValueError in template %s' % chosen)
            return "Error reported!"
        except TypeError:
            self.vileerror('TypeError in template %s' % chosen)
            return "Error reported!"
        except:
            self.vileerror('Unidentified exception while processing template %s. Please report this.' % chosen)
            return "Error reported!"

def report_callback_exception(self, exc, val, tb):
    """Internal function. It reports exception on sys.stderr."""
#    import traceback, sys
    builder = cStringIO.StringIO()
    builder.write("Platform: %s\n\n" % platform())
   
#    sys.stderr.write("Exception in Tkinter callback\n")
    sys.last_type = exc
    sys.last_value = val
    sys.last_traceback = tb
    traceback.print_exception(exc, val, tb, file=builder)
    e = ExceptionBox(self, "Exception", builder.getvalue())

if __name__ == '__main__':
    # Import Psyco if available
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass

    Tk.report_callback_exception = report_callback_exception
    root = Tk()
    app = App(root)
    if hasattr(sys, 'frozen'):
        if getattr(sys, 'frozen', None) in ('macosx_app',):
            root.tk.call('console', 'hide')
    
    u = rC.rClick(root, '------')
    root.mainloop()

#    except:
#        builder = cStringIO.StringIO()
       
#        traceback.print_exc(file=builder)
#        e = ExceptionBox(root, "Exception", builder.getvalue())