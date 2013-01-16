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
        """ Az osztály definiáláskor a megadott érték hozzárendelése a változóhoz """
        self.var = var
        
    def get(self):
        """ Változó értékének lekérése """
        return self.var
        
    def set(self, var):
        """ Változó értéknek módosítása """
        self.var = var

class dropbox(session.DropboxSession):
    def link(self, token):
        """ Új link létrehozása a Dropbox és a JamCrop között """
        self.obtain_access_token(token)
        configRoot.find('token').text = "|".join([self.token.key, self.token.secret])
        
    def auth(self):
        """ Link kérése a Dropboxtól """
        token = self.obtain_request_token()
        webbrowser.open(self.build_authorize_url(token))
        return(token)

    def unlink(self):
        """ A jelenlegi link törlése """
        configRoot.find('token').text = None
        session.DropboxSession.unlink(self)
        
    def load(self):
        """ Mentett link betöltése """
        if(configRoot.find('token').text != None):
            try:
                self.set_token(*configRoot.find('token').text.split('|'))
                return(1)
            except: pass
        return(0)
        
class window():
    def entry(self, root, x, y, w, default, var = None, text = None):
        """ Új entry létrehozása - @var: StringVar, @text: String """
        if(var != None): entry = Tkinter.Entry(root, textvariable = var, width = w)
        elif(text != None): entry = Tkinter.Entry(root, text = text, width = w)
        if(default != None): entry.insert(0, default)
        entry.place(x = x, y = y)
        return(entry)
        
    def label(self, root, x, y, text):
        """ Új label létrehozása """
        label = Tkinter.Label(root, text = text)
        label.place(x = x, y = y)
        return(label)
        
    def button(self, root, x, y, w, var = None, text = None):
        """ Új gomb létrehozása """
        if(var != None): button = Tkinter.Button(root, textvariable = var, width = w)
        elif(text != None): button = Tkinter.Button(root, text = text, width = w)
        button.place(x = x, y = y)
        return(button)
        
    def menu(self, root, x, y, w, var, values):
        """ Új menü létrehozása """
        menu = apply(Tkinter.OptionMenu, (root, var) + tuple(values))
        menu.config(width = w)
        menu.place(x = x, y = y)
        return(menu)
        
    def check(self, root, x, y, var, on, off):
        """ Csekkoló gomb létrehozása """
        check = Tkinter.Checkbutton(root, variable = var, offvalue = off, onvalue = on)
        check.place(x = x, y = y)
        return(check)
        
class configWindow(Tkinter.Toplevel, window):
    def __init__(self, parent, session, status = reference(0)):
        """ Beállítások ablak megjelenítése (és változóinak iniciálása) """
        Tkinter.Toplevel.__init__(self, parent, width = 195, height = 85)
        self.protocol('WM_DELETE_WINDOW', lambda: self.deleteEvent(status))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-toolwindow', 1)
        self.wm_attributes("-topmost", 1)
        self.title(u"Beállítások")
        self.wm_iconbitmap(ICON)
        
        # URL automatikus másolását vezérlő check gomb létrehozása
        self.label(self, 5, 5, "URL automatikus másolása:")
        copyValue = Tkinter.StringVar()
        copyCheck = self.check(self, 172, 5, copyValue, 'true', 'false')
        copyValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setCopy(varName, elementName, mode, copyValue))
        if(configRoot.find('copy').text == 'false'): copyCheck.deselect()
        
        # Képformátumokat tartalmazó lista létrehozása
        self.label(self, 5, 30, "Képformátum:")
        formatValue = Tkinter.StringVar()
        formatValue.set(configRoot.find('format').text)
        formatMenu = self.menu(self, 93, 25, 9, formatValue, ['jpg', 'png', 'gif'])
        formatValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setFormat(varName, elementName, mode, formatValue))
        
        # Leválasztást végrehajtó gomb létrehozása
        button = self.button(self, 5, 55, 25, text = "JamCrop leválasztása")
        button.bind("<Button-1>", lambda event: self.doUnlink(event, parent, session))
        
        status.set(1)
        
    def deleteEvent(self, status):
        """ Ablak bezárását végrehajtó függvény """
        status.set(0)
        self.destroy()
        
    def setCopy(self, varName, elementName, mode, value):
        """ URL másolás beállításának módosítása """
        configRoot.find('copy').text = unicode(value.get())
        
    def setFormat(self, varName, elementName, mode, value):
        """ Azonosító módosítása """
        configRoot.find('format').text = unicode(value.get())
        
    def doUnlink(self, event, parent, session):
        """ JamCrop lecsatlakoztatása és a főablak bezárása """
        session.unlink()
        parent.deleteEvent()
        
class grabWindow(Tkinter.Tk):
    disabled = reference(0)
    x, y, last = 0, 0, 0
    square, session = None, None

    def __init__(self): 
        """ A főablak megjelenítése és változóinak iniciálása """
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
            
            token = self.session.auth()
            if(tkMessageBox.askokcancel(title = "JamCrop", message = "A JamCrop működéséhez, szüksége van egy korlátozott Dropbox hozzáférésre. Amennyiben engedélyezted a kapcsolódását a Dropboxhoz az automatikusan megnyílt oldalon, kattintás az OK-ra.\n\nA beállítások ablakot az összekapcsolás után, az F1 billentyű megnyomásával érheted el.")):
                try: self.session.link(token)
                except: return
            else: return
            
            self.update()
            self.deiconify()
        
    def deleteEvent(self):
        """ A főblak bezárását végrehajtó függvény. """
        configHandler.write(CONFIG)
        self.destroy()
    
    def autoFocus(self):
        """ Főablak automatikus felemelése - 250 msenként """
        if(self.disabled.get()):
            self.wm_attributes("-topmost", 0)
        else:
            self.wm_attributes("-topmost", 1)
            self.tkraise()
            self.focus()
        self.after(250, self.autoFocus)
    
    def keyPress(self, event):
        """ Billentyűleütések feldolgozásáért felelős függvény """
        if(event.keysym == 'Escape'):
            self.deleteEvent()
        elif(event.keysym == 'F1' and not self.disabled.get()):
            config = configWindow(self, self.session, self.disabled)
            config.mainloop()

    def drawSquare(self, event):
        """ Kijelölő négyzet kirajzolása grafikusan az adott egérpozíció alapján. """
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
        """ Leendő képernyőkép koordinátáinak kijelöléséért felelős függvény. """
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
        """ Képernyőkép elkészítése a megadott koordináták alapján """
        self.withdraw()
        connection = client.DropboxClient(self.session)
        
        fileName = time.strftime('%Y_%m_%d_%H_%M_%S') + '.' + configRoot.find('format').text;
        ImageGrab.grab((x1, y1, x2, y2)).save(fileName)
        connection.put_file(fileName, open(os.path.expanduser(fileName), "rb"))
        os.unlink(fileName)
        
        result = connection.share(fileName)
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