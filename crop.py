#!/usr/bin/env python
#-*- coding: utf-8 -*-

CONFIG      = 'config.xml'
ICON        = 'icon.ico'
APP_KEY     = '***REMOVED***'
APP_SECRET  = '***REMOVED***'

import Tkinter, xml.etree.ElementTree as xml, time, os, webbrowser, tkMessageBox
from dropbox import client, rest, session
from pil import ImageGrab

configHandler = xml.parse(CONFIG)
configRoot = configHandler.getroot()

class reference():
    def __init__(self, var):
        """ Initializing the variable, when you define the class"""
        self.var = var
        
    def get(self):
        """ Get the value of the variable """
        return self.var
        
    def set(self, var):
        """ Set he value of the variable """
        self.var = var

class dropbox(session.DropboxSession):
    def verify(self):
        """ Get the verification link and the token from Dropbox """
        token = self.obtain_request_token()
        webbrowser.open(self.build_authorize_url(token))
        return(token)
        
    def link(self, token):
        """ Create a new link between Dropbox and JamCrop """
        self.obtain_access_token(token)
        configRoot.find('token').text = "|".join([self.token.key, self.token.secret])

    def unlink(self):
        """ Unlink the JamCrop from Dropbox """
        configRoot.find('token').text = None
        session.DropboxSession.unlink(self)
        
    def load(self):
        """ Load the saved link from token """
        if(configRoot.find('token').text != None):
            try:
                self.set_token(*configRoot.find('token').text.split('|'))
                return(1)
            except: pass
        return(0)
        
class window():
    def entry(self, root, x, y, w, default, var = None, text = None):
        """ Create a new entry (@var: StringVar; @text: String;) """
        if(var != None): entry = Tkinter.Entry(root, textvariable = var, width = w)
        elif(text != None): entry = Tkinter.Entry(root, text = text, width = w)
        if(default != None): entry.insert(0, default)
        entry.place(x = x, y = y)
        return(entry)
        
    def label(self, root, x, y, text):
        """ Create a new label """
        label = Tkinter.Label(root, text = text)
        label.place(x = x, y = y)
        return(label)
        
    def button(self, root, x, y, w, var = None, text = None):
        """ Create a new button (@var: StringVar; @text: String;) """
        if(var != None): button = Tkinter.Button(root, textvariable = var, width = w)
        elif(text != None): button = Tkinter.Button(root, text = text, width = w)
        button.place(x = x, y = y)
        return(button)
        
    def menu(self, root, x, y, w, var, values):
        """ Create a new menu (@var: StringVar; @values: Array;) """
        menu = apply(Tkinter.OptionMenu, (root, var) + tuple(values))
        menu.config(width = w)
        menu.place(x = x, y = y)
        return(menu)
        
    def check(self, root, x, y, var, on, off):
        """ Create a new checkbox """
        check = Tkinter.Checkbutton(root, variable = var, offvalue = off, onvalue = on)
        check.place(x = x, y = y)
        return(check)
        
class configWindow(Tkinter.Toplevel, window):
    def __init__(self, parent, session, status = reference(0)):
        """ Initializing the config windows """
        Tkinter.Toplevel.__init__(self, parent, width = 195, height = 110)
        self.protocol('WM_DELETE_WINDOW', lambda: self.deleteEvent(status))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-toolwindow', 1)
        self.wm_attributes("-topmost", 1)
        self.title(u"Configuration")
        self.wm_iconbitmap(ICON)
        
        # Create the automatic url copy checkbox
        self.label(self, 5, 5, "Automatic URL copy:")
        copyValue = Tkinter.StringVar()
        copyCheck = self.check(self, 172, 5, copyValue, 'true', 'false')
        copyValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setCopy(varName, elementName, mode, copyValue))
        if(configRoot.find('copy').text == 'false'): copyCheck.deselect()
		
        # Create the browser behavor checkbox
        self.label(self, 5, 30, "Open in the browser:")
        shortValue = Tkinter.StringVar()
        shortCheck = self.check(self, 172, 30, shortValue, 'true', 'false')
        shortValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setBrowser(varName, elementName, mode, shortValue))
        if(configRoot.find('browser').text == 'false'): shortCheck.deselect()
        
        # Create the list of image formats
        self.label(self, 5, 55, "Image format:")
        formatValue = Tkinter.StringVar()
        formatValue.set(configRoot.find('format').text)
        formatMenu = self.menu(self, 93, 50, 9, formatValue, ['jpg', 'png', 'gif'])
        formatValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setFormat(varName, elementName, mode, formatValue))
        
        # Create the button for unlink the applcation
        button = self.button(self, 5, 80, 25, text = "Unlink JamCrop")
        button.bind("<Button-1>", lambda event: self.doUnlink(event, parent, session))
        
        status.set(1)
        
    def deleteEvent(self, status):
        """ Configuration window closing function """
        status.set(0)
        self.destroy()
        
    def setCopy(self, varName, elementName, mode, value):
        """ Set the url copy paramter """
        configRoot.find('copy').text = unicode(value.get())
        
    def setBrowser(self, varName, elementName, mode, value):
        """ Set the browser parameter """
        configRoot.find('browser').text = unicode(value.get())
        
    def setFormat(self, varName, elementName, mode, value):
        """ Change the format parameter """
        configRoot.find('format').text = unicode(value.get())
        
    def doUnlink(self, event, parent, session):
        """ Unlink JamCrop from Dropbox, and close the windows """
        session.unlink()
        parent.deleteEvent()
        
class grabWindow(Tkinter.Tk):
    disabled = reference(0)
    x, y, last = 0, 0, 0
    square, session = None, None

    def __init__(self): 
        """ Initializing the grab windows of the application """
        Tkinter.Tk.__init__(self)
        self.protocol('WM_DELETE_WINDOW', self.deleteEvent)
        self.configure(background = 'white')
        self.wm_attributes("-topmost", 1)
        self.attributes('-fullscreen', 1)
        self.attributes('-alpha', 0.15)
        self.wm_iconbitmap(ICON)
        self.title(u"JamCrop")
		
        self.bind("<Button-1>", self.click)
        self.bind_all('<Key>', self.keyPress)
        self.square = Tkinter.Canvas(self, width = 0, height = 0, bg = 'black')
        
        self.session = dropbox(APP_KEY, APP_SECRET, access_type = 'app_folder')
        if(not self.session.load()):
            self.withdraw()
            
            token = self.session.verify()
            if(tkMessageBox.askokcancel(title = "JamCrop", message = "The JamCrop require a limited Dropbox access for itself. If you allowed the connection to the Dropbox, from the recently appeared browser window, please click on the OK button. After the grab windows have shown, you can open the configuration windows by pressing the F1 button.")):
                try: self.session.link(token)
                except: return
            else: return
            
            self.update()
            self.deiconify()
        
    def deleteEvent(self):
        """ Closing function for the grab window """
        configHandler.write(CONFIG)
        self.destroy()
    
    def autoFocus(self):
        """ Automatic focus for the grab window """
        if(self.disabled.get()):
            self.wm_attributes("-topmost", 0)
        else:
            self.wm_attributes("-topmost", 1)
            self.tkraise()
            self.focus()
        self.after(250, self.autoFocus)
    
    def keyPress(self, event):
        """ Parse the key presses """
        if(event.keysym == 'Escape'):
            self.deleteEvent()
        elif(event.keysym == 'F1' and not self.disabled.get()):
            config = configWindow(self, self.session, self.disabled)
            config.mainloop()

    def drawSquare(self, event):
        """ Draw the selecting square on to the grab window """
        if(self.x < event.x_root and self.y < event.y_root):
            self.square.config(width = event.x_root-self.x, height = event.y_root-self.y)
            self.square.place(x = self.x, y = self.y)
        elif(self.x > event.x_root and self.y > event.y_root):
            self.square.config(width = self.x-event.x_root, height = self.y-event.y_root)
            self.square.place(x = event.x_root, y = event.y_root)
        elif(self.x < event.x_root and self.y > event.y_root):
            self.square.config(width = event.x_root-self.x, height = self.y-event.y_root)
            self.square.place(x = self.x, y = event.y_root)
        elif(self.x > event.x_root and self.y < event.y_root):
            self.square.config(width = self.x-event.x_root, height = event.y_root-self.y)
            self.square.place(x = event.x_root, y = self.y)
        else:
            self.square.place_forget()
    
    def click(self, event):
        """ Set the coordinates of the screenshot """
        if(not self.disabled.get() and not self.last):
            self.bind("<Motion>", self.drawSquare)
            self.x = event.x_root
            self.y = event.y_root
            self.last = 1;
        elif(not self.disabled.get()):
            if(self.x < event.x_root and self.y < event.y_root):
                self.grab(self.x, self.y, event.x_root, event.y_root)
            elif(self.x > event.x_root and self.y > event.y_root):
                self.grab(event.x_root, event.y_root, self.x, self.y)
            elif(self.x < event.x_root and self.y > event.y_root):
                self.grab(self.x, event.y_root, event.x_root, self.y)
            elif(self.x > event.x_root and self.y < event.y_root):
                self.grab(event.x_root, self.y, self.x, event.y_root)
            else:
                self.unbind("<Motion>")
                self.square.place_forget()
                self.last = 0;
       
    def grab(self, x1, y1, x2, y2):
        """ Create the screenshot from the coordinates """
        self.withdraw()
        connection = client.DropboxClient(self.session)
        
        fileName = time.strftime('%Y_%m_%d_%H_%M_%S') + '.' + configRoot.find('format').text;
        ImageGrab.grab((x1, y1, x2, y2)).save(fileName)
        connection.put_file(fileName, open(os.path.expanduser(fileName), "rb"))
        os.unlink(fileName)
        result = connection.share(fileName)
        
        if(configRoot.find('browser').text == 'true'):
			webbrowser.open(result['url'])
        if(configRoot.find('copy').text == 'true'):
            self.clipboard_clear()
            self.clipboard_append(result['url'])
        
        self.deleteEvent()

def main():
    crop = grabWindow()
    crop.autoFocus()
    crop.mainloop()

if(__name__ == '__main__'):
    main()