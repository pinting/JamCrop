#!/usr/bin/env python
#-*- coding: utf-8 -*-

SERVER = 'jamcropxy.appspot.com'
CONFIG = 'config.xml'
ICON = 'icon.ico'

import Tkinter, xml.etree.ElementTree as xml, time, os, webbrowser, tkMessageBox, urllib, urllib2, urlparse
from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from pil import ImageGrab

register_openers()

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

class dropbox():
    request_token = None
    access_token = None
        
    def authorize(self):
        """ Get the verification link from Dropbox """
        result = urllib2.urlopen('https://%s/authorize' % SERVER)
        self.request_token = dict(urlparse.parse_qsl(result.read()))
        return(self.request_token)
    
    def access(self):
        """ Create a new link between Dropbox and JamCrop """
        result = urllib2.urlopen('%s?%s' % ('https://%s/access' % SERVER, urllib.urlencode(self.request_token)))
        self.access_token = dict(urlparse.parse_qsl(result.read()))
        return(self.access_token)

    def unlink(self):
        """ Unlink the JamCrop from Dropbox """
        config.getroot().find('token').text = None
        self.request_token = None
        self.access_token = None

    def upload(self, file):
        datagen, headers = multipart_encode({'body': open(file, 'rb')})
        request = urllib2.Request('%s?%s' % ('https://%s/upload' % SERVER, 
                                  urllib.urlencode(dict(self.access_token.items() + dict({'name' : file}).items()))), datagen, headers)
        return(urllib2.urlopen(request))

    def share(self, file, short = 'false'):
        request = urllib2.Request('%s?%s' % ('https://%s/share' % SERVER, 
                                  urllib.urlencode(dict(self.access_token.items() + dict({'name' : file, 'short' : short}).items()))))
        return(urllib2.urlopen(request))
        
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
        
class tooltip(Tkinter.Toplevel, window):
    def __init__(self, parent, message, timeout = 1500):
        """ Initializing the config window """
        Tkinter.Toplevel.__init__(self, parent, bg = 'black')
        self.overrideredirect(1)
        self.geometry("%dx%d%+d%+d" % (128, 24, self.winfo_screenwidth()-128, 0))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-alpha', 0.75)
        self.wm_attributes("-topmost", 1)
        
        self.bind("<Button-1>", lambda event: self.destroy())
        self.after(timeout, self.destroy)
        
        message = self.label(self, 5, 0, message)
        message.config(bg = "black", fg = "white")
        
class configWindow(Tkinter.Toplevel, window):
    def __init__(self, parent, session, status = reference(0)):
        """ Initializing the config window """
        Tkinter.Toplevel.__init__(self, parent, width = 195, height = 135)
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
        if(config.getroot().find('copy').text == 'false'): copyCheck.deselect()
		
        # Create the browser behavior checkbox
        self.label(self, 5, 30, "Open in the browser:")
        shortValue = Tkinter.StringVar()
        shortCheck = self.check(self, 172, 30, shortValue, 'true', 'false')
        shortValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setBrowser(varName, elementName, mode, shortValue))
        if(config.getroot().find('browser').text == 'false'): shortCheck.deselect()
		
        # Create the tooltip checkbox
        self.label(self, 5, 55, "Show a tooltip:")
        tooltipValue = Tkinter.StringVar()
        tooltipCheck = self.check(self, 172, 55, tooltipValue, 'true', 'false')
        tooltipValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setTooltip(varName, elementName, mode, tooltipValue))
        if(config.getroot().find('tooltip').text == 'false'): tooltipCheck.deselect()
        
        # Create the list of image formats
        self.label(self, 5, 80, "Image format:")
        formatValue = Tkinter.StringVar()
        formatValue.set(config.getroot().find('format').text)
        formatMenu = self.menu(self, 93, 75, 9, formatValue, ['jpg', 'png', 'gif'])
        formatValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setFormat(varName, elementName, mode, formatValue))
        
        # Create the button to unlink the application
        button = self.button(self, 5, 105, 25, text = "Unlink from Dropbox")
        button.bind("<Button-1>", lambda event: self.doUnlink(event, parent, session))
        
        status.set(1)
        
    def deleteEvent(self, status):
        """ Configuration window closing function """
        status.set(0)
        self.destroy()
        
    def setCopy(self, varName, elementName, mode, value):
        """ Set the url copy paramter """
        config.getroot().find('copy').text = unicode(value.get())
        
    def setBrowser(self, varName, elementName, mode, value):
        """ Set the browser parameter """
        config.getroot().find('browser').text = unicode(value.get())
        
    def setTooltip(self, varName, elementName, mode, value):
        """ Set the tooltop parameter """
        config.getroot().find('tooltip').text = unicode(value.get())
        
    def setFormat(self, varName, elementName, mode, value):
        """ Change the format parameter """
        config.getroot().find('format').text = unicode(value.get())
        
    def doUnlink(self, event, parent, session):
        """ Unlink JamCrop from Dropbox, and close the window """
        session.unlink()
        parent.deleteEvent()
        
class grabWindow(Tkinter.Tk):
    disabled = reference(0)
    x, y, last = 0, 0, 0
    square, session = None, None

    def __init__(self): 
        """ Initializing the grab window of the application """
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
        
        self.withdraw()
        
        self.session = dropbox()
        request_token = self.session.authorize()
        webbrowser.open("%s?%s" % ("https://www.dropbox.com/1/oauth/authorize", urllib.urlencode({'oauth_token' : request_token['oauth_token']})))
        
        if(tkMessageBox.askokcancel(title = "JamCrop", message = "The JamCrop require a limited Dropbox access for itself. If you allowed the connection to the Dropbox, from the recently appeared browser window, please click on the OK button. After the grab window have shown, you can open the configuration window by pressing the F1 button.")):
            try: self.session.access()
            except: return
        else: return
        
        self.update()
        self.deiconify()
        
    def deleteEvent(self):
        """ Closing function for the grab window """
        config.write(CONFIG)
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
        """ Track the key presses """
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
        
        fileName = time.strftime('%Y_%m_%d_%H_%M_%S') + '.' + config.getroot().find('format').text;
        ImageGrab.grab((x1, y1, x2, y2)).save(fileName)
        self.session.upload(fileName)
        os.unlink(fileName)
        result = self.session.share(fileName)
        
        if(config.getroot().find('copy').text == 'true'):
            self.clipboard_clear()
            self.clipboard_append(result['url'])
        if(config.getroot().find('browser').text == 'true'):
			webbrowser.open(result['url'])
        if(config.getroot().find('tooltip').text == 'true'):
            alert = tooltip(self, "The uploading is completed", 2500)
            alert.geometry("%dx%d%+d%+d" % (160, 25, self.winfo_screenwidth()-160, 0))
            alert.mainloop()
        
        self.deleteEvent()

def main():
    crop = grabWindow()
    crop.autoFocus()
    crop.mainloop()

if(__name__ == '__main__'):
    config = xml.parse(CONFIG)
    main()