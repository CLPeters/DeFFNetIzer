#m04405a12:02 class to provide Tk right click menu
#import rClickclass as rC
#then do something like u = rC.rClick(root, "Pmwdemo")
#before root.mainlooop()
#add ,name= 'lbb'  to any listbox to avoid an error with paste on those
#later versions will detect and disable those menu items
#should be a way to create the menu once and just config it at post time
#add sample manual _test for PMW, Tix & Tk
#explore usage in Qt, wx, GTK if they like Qt have rclick can items be added?
#add ini reading of options and better naming of widgets maybe interactively
#produce patches for many of the popular Tk tools adding rClick
#easygui patch, anygui patch for Tk backend at least.

import Tkinter as Tk

__version__ = '0.102'

# 
# + helpers
#     - get_selection_indices
#     - has_selection
# 
# AtEnd()
# refers to the last position in the text
# 
# AtInsert()
# refers to the point where the text cursor is
# 
# AtSelFirst()
# indicates the beginning point of the selected text
# 
# AtSelLast()
# denotes the last point of the selected text and finally
# 
# At(x[, y])
# refers to the character at pixel location x, y (with y not used in the case 
# of a text entry widget, which contains a single line of text).

def get_selection_indices(e):  #from Idle
    try:
        first = e.widget.index("sel.first")
        last = e.widget.index("sel.last")
        return first, last
    except Tk.TclError:
        return None, None

def has_selection(e):  #kluge
    try:
        try:
            selection_get = e.widget.selection_get

        except AttributeError:

            selection_get = e.widget.select_get
    
        #if e.widget.selection_present(): noavail in Text
        s = selection_get() #eventually find a better way
        return s
    except Tk.TclError:
        pass
    return None

class rClick:
    ''' 
        default right click context menu for all Tk Entry and Text widgets
        this could be a sourceforge project on its own
        planning to be a module, you import then maybe subclass
        override some or all of the methods
        instantiate it. it binds B3
        future plans keep track of instances so each leo can have its own
        for simple Tk apps they only need one and usually only c&p
        maybe a submenu of specilized insert strings
        this is definatly not the final refactor
        I should study some other menu classes and add some testing
    '''
    # 
    # + rClick
    #     + Methods
    #         - __init__
    #         - rClick_Copy
    #         - rClick_Cut
    #         - rClick_Paste
    #         - rClick_Del
    #         - rClick_insert
    #     - rC_nclst
    #     - rC_menu
    #     - rC_config
    #     - rClicker
    #     - rClickbinder
    
    def __init__(self, tKrooT, label= '',
                       toggleVar= 1, toggle_label= 'toggle' ):
        #tKrooT=Tk.TopLevel()?
        
        self.toggleVar = toggleVar  #not sure what this might accomplish
        self.toggle_label = toggle_label
        self.label = label
        self.rClickbinder(tKrooT)
        self.e = None
    
    def rClick_Copy(self, apnd= 0 ):
        self.e.widget.event_generate('<Control-c>' )
    
    def rClick_Cut(self ):
        self.e.widget.event_generate('<Control-x>' )
    
    def rClick_Paste(self ): 
        self.e.widget.event_generate('<Control-v>' )
    
    def rClick_Del(self ):
        s = has_selection(self.e )
        if s:
            first, last = get_selection_indices(self.e )
            self.e.widget.delete(first, last )
    
    def rClick_insert(self, s ): #insert s at the current curser position
        self.e.widget.insert("insert",s )
    
    def rC_nclst(self ):
        nclst=[
            ('------',None),
            (' Cut', self.rClick_Cut ),  
            (' Copy', self.rClick_Copy ),
            (' Paste', self.rClick_Paste ),
            #(' Delete', self.rClick_Del ),
            #('------',None),      
            ]
        return nclst
    
    def rC_menu(self, nclst): 
    
        #add a preparse to ensure no infinate recursion and well formed
        #text,commands in menu tupples.
    
        try:
            rmenu = Tk.Menu(None, tearoff= 0, takefocus= 0 )
            cas = {}
            cascade = 0
            for (txt, cmd) in nclst:
                if txt.startswith('>>>>>>') or cascade:
                    if txt.startswith('>>>>>>') and cascade and cmd == None:
                        #done cascade
                        cascade = 0
                        rmenu.add_cascade(label= icmd, menu= cas[icmd] )
            
                    elif cascade:
                        if txt == ' ------ ':
                            cas[icmd].add_separator()
                            
                        else: cas[icmd].add_command(label= txt, command= cmd )
            
                    else:  # start cascade
                        cascade = 1
                        icmd = cmd[:]
                        cas[icmd] = Tk.Menu(rmenu, tearoff= 0, takefocus= 0 )
                else:
                    if txt == ' ------ ':
                        rmenu.add_separator()
                    else: rmenu.add_command(label= txt, command= cmd )
    
        except (Tk.TclError, TypeError, AttributeError):
            rmenu = Tk.Menu(None, tearoff= 0, takefocus= 0 )
            rmenu.add_command(label= ' Copy', command= self.rClick_Copy )
    
        return rmenu
    
    def rC_config(self, rmenu ): 
        try:
    
            rmenu.entryconfigure(0, state= 'disabled' )
            rmenu.entryconfigure(0, label= self.label )
        
            #kindof hardwired but its just a demo
            #the better way is to ask the menu for a list
            #or only create a list with copy in it...
            if self.e.widget._name == 'lbb':
                #active, normal, or disabled
        
                rmenu.activate("none" )
                rmenu.entryconfigure(' Copy', state= 'normal' )
                rmenu.entryconfigure('Copy', state= 'disabled' )
                rmenu.entryconfigure('Cut', state= 'disabled' )
        
                #for i in range(1,len(nclst)-3 ):
                #    if i == 2: continue #allow copy, disable the others
                #    rmenu.entryconfigure(i, state= 'disabled' )
        
         #   rmenu.add_checkbutton(label= self.toggle_label, variable= self.toggleVar )
        except (Tk.TclError, TypeError, AttributeError):
            pass
    
    def rClicker(self, e ):
    
        self.e = e
        e.widget.focus()
    
        #how to abstract this if it needs e for its functions?
        nclst = self.rC_nclst()  
    
        #pass it the command list and return the Tk menu  
        #not sure how this worked outside the class parsing self.command  
        rmenu = self.rC_menu(nclst )
    
        #pass it the command list & event and possibly modify Tk menu
        #users can override this to provide per widget options
        #like greying out options etc
        self.rC_config(rmenu )
    
        #possibly need an unpost if loose focus
        rmenu.tk_popup(e.x_root-3, e.y_root+3,entry= "0" )
    
        return "break"
    
    def rClickbinder(self, r ):
        for b in [ 'Text', 'Entry', 'Listbox', 'Label']:  # 
            r.bind_class(b, sequence= '<Button-3>',
                              func= self.rClicker, add= '' )
# 
# I wonder can I spawnl each of these to test all at once?
# + test status
#   need to add Entry,Text,Lable & Listbox to all
#   and if possible automate the test somehow
#   also have to show how to subclass and change nclst & config
# 
#   at least to prove all the binds are taking place.
# 
#   tested with win98 py2.33 from python.org
#     -  Tix_test()   Tix is in the help, I can import but error's
#     -  PMW_test()   works
#     -  anygui_test()    sets Tk backend, rClick up but copy ineffective
#                         probably it does something with the clicpboard
#                         or forgets to set the ^c binds on listbox?
#     -  TK_test()    works

def Tix_test():    #http://Tix.sourceforge.net
    import Tix
    import rClickclass as rC
    root = Tix.Tk()
    #root.tk.eval('package require Tix')

    class App(Tix.Frame):
        def __init__(self, master=None):
            Tk.Frame.__init__(self, master)
            self.pack()
            self.entrythingy = Tix.Entry().pack()
            self.Listthingy = Tix.Listbox(name= 'lbb').pack()

    myapp = App()
    
    myapp.master.title(" Tix_test App")
    
    #u = rC.rClick(myapp, " Tix_test")
    myapp.mainloop()

def PMW_test():  #http://download.sourceforge.net/pmw
    '''parts stolen from Tkinter list
    '''
    import Tkinter as Tk
    import Pmw
    import rClickclass as rC

    root = Tk.Tk()
    root.title('Tool')
    Pmw.initialise(root)
    
    Mainframe = Tk.Frame(root, width=215, height=210)
    class AtsMenuBar:
        def __init__(self):
            menuBar=Pmw.MenuBar(Mainframe, hull_relief='raised', hull_borderwidth=1)
            menuBar.pack(fill='x')
        
            sc2 = Pmw.ScrolledFrame(Mainframe)  #
            sc2.pack(fill='x', expand=1, padx=2, pady=2)
            sc2.place(relx=0.25, rely=0.25, anchor='nw')
            HashBox1 = Pmw.EntryField(sc2.interior(), labelpos='w', labelmargin=1,
         validate = None)
        
            HashBox1.pack(fill='x', expand=1, padx=1, pady=1)
            
                
    menu = AtsMenuBar()
    Mainframe.pack(fill = 'both', expand = 1, padx = 5, pady = 5)
    Mainframe.pack_propagate(0)
    
    u = rC.rClick(root, "PMW_test")
    root.mainloop()

def anygui_test(g= 'tkgui' ):
    '''http://anygui.sourceforge.net
    In [1]: from anygui import *
    In [2]: backend()
    Out[2]: 'msw'
    PythonWin  (mswgui)    {http://starship.python.net/crew/mhammond/win32}
    Tkinter    (tkgui)     {http://www.python.org/topics/tkinter}
    wxPython   (wxgui)     {http://www.wxpython.org}
    Java Swing (javagui)   {http://www.jython.org}
    PyGTK      (gtkgui)    {http://www.daa.com.au/~james/pygtk}
    Bethon     (beosgui)   {http://www.bebits.com/app/1564}
    PyQt       (qtgui)     {http://www.thekompany.com/projects/pykde}
    Curses     (cursesgui) -- used when no GUI package is available
    Plain text (textgui)   -- used if curses is not available
    'msw gtk java wx tk beos qt curses text'
: On some platforms, including FreeBSD and Mac OS X, setting environ may cause memory leaks. Refer to the system documentation for putenv
    {http://www.anygui.org}, subscribe to the developer's mailing list (devel@anygui.org) and the user's list (users@anygui.org), and try to familiarise yourself with how the package works behind the scenes. 
        '''
    import os
    os.environ['ANYGUI_WISHLIST'] = 'tk wx * text curses' 

    #import anygui.backends.tkgui as gui
    import anygui as gui
    import rClickclass as rC

    app = gui.Application()

    btn = gui.Button(text= 'Hello' )
    lbx = gui.ListBox()
    lbx.items = 'first second third'.split() 
    TextA = gui.TextArea()

    win = gui.Window(size= (200,100) )
    win.add(btn, left= 0, top= 0, right= 0, bottom= 0, hstretch= 1, vstretch= 0 )
    win.add(lbx, hstretch= 1, vstretch= 0 )
    win.add(TextA, hstretch= 1, vstretch= 0 )

    app.add(win)

    u = rC.rClick(app._root, "anygui_test")
    app.run()

def Tk_test():
    ''' from the help
    '''
    import Tkinter as Tk
    import rClickclass as rC
    class App(Tk.Frame):
        def __init__(self, master=None):
            Tk.Frame.__init__(self, master)
            self.pack()
            self.entrythingy = Tk.Entry().pack()
            self.Listthingy = Tk.Listbox(name= 'lbb').pack()

    myapp = App()
    
    myapp.master.title("_test App")
    
    u = rC.rClick(myapp, "Tk_test")
    myapp.mainloop()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        im = sys.argv[1].lower()
        if im == 'tix':         Tix_test()
        elif im == 'pmw':       PMW_test()
        elif im == 'any':    anygui_test()
        else:
            print 'Tix Pmw or default test Tk _test()'

    else:
        Tk_test()

#end