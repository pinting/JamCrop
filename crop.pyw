#!/usr/bin/env python
#-*- coding: utf-8 -*-

__author__ = "Tornyi Dénes"
__version__ = "1.1.0"


SERVERS = ['jamcropxy.appspot.com', 'jamcropxy-pinting.rhcloud.com']
CONFIG = 'config.xml'
ICON = 'icon.ico'
TIMEOUT = 2500


from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from xml.etree.ElementTree import ElementTree
from PIL import ImageGrab
import tkMessageBox
import webbrowser
import urlparse
import Tkinter
import urllib2
import urllib
import json
import time
import sys
import os


register_openers()


class Reference:
    def __init__(self, var):

        """ Set the variable, when initializing the class"""

        self.var = var

    def get(self):

        """ Get the value of the variable """

        return self.var

    def set(self, var):

        """ Set the value of the variable """

        self.var = var


class Connection:
    request_token = None
    access_token = None
    config = None

    def __init__(self, config):

        """ Get the config file
        :param config: The loaded config
        """

        self.config = config

    def authorize(self):

        """ Get a request token """

        result = urllib2.urlopen('https://%s/authorize' % self.config['server'])
        self.request_token = dict(urlparse.parse_qsl(result.read()))
        return self.request_token

    def access(self):

        """ Get an access token with the request token """

        result = urllib2.urlopen('%s?%s' % ('https://%s/access' % self.config['server'],
                                            urllib.urlencode(self.request_token)))
        self.access_token = dict(urlparse.parse_qsl(result.read()))
        self.config['token'] = urllib.urlencode(self.access_token)
        return self.access_token

    def load(self):

        """ Load the previously saved access token """

        if self.config['token'] is not None:
            self.access_token = dict(urlparse.parse_qsl(self.config['token']))
            return True
        else:
            return False

    def unlink(self):

        """ Delete token from the config """

        self.config['token'] = None

    def upload(self, fileName):

        """ Upload a file to the server
        :param fileName: Name of the file for upload
        """

        body, headers = multipart_encode({'body': open(fileName, 'rb')})
        request = urllib2.Request('%s?%s' % ('https://%s/upload' % self.config['server'],
                                             urllib.urlencode(dict(self.access_token.items() +
                                                                   dict({'name': fileName}).items()))), body, headers)
        return json.loads(urllib2.urlopen(request).read())

    def share(self, fileName, short = 'false'):

        """ Get the link of an uploaded file
        :param fileName: Name of the file for share
        :param short: Get short or long URL
        """

        request = urllib2.Request('%s?%s' % ('https://%s/share' % self.config['server'],
                                  urllib.urlencode(dict(self.access_token.items() +
                                                        dict({'name': fileName, 'short': short}).items()))))
        return json.loads((urllib2.urlopen(request)).read())


class Window():
    def entry(self, root, x, y, w, default, var = None, text = None):

        """ Create a new entry
        :param root: Parent window
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param w: Width of the entry
        :param default: Default value
        :param var: StringVar as the entry value (it can be changed later)
        :param text: String as the entry value
        """

        entry = None

        if(var is not None):
            entry = Tkinter.Entry(root, textvariable = var, width = w)
        elif(text is not None):
            entry = Tkinter.Entry(root, text = text, width = w)
        if(default is not None):
            entry.insert(0, default)

        entry.place(x = x, y = y)
        return entry

    def label(self, root, x, y, text):

        """ Create a new label
        :param root: Parent window
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param text: Content of the label
        """

        label = Tkinter.Label(root, text = text)
        label.place(x = x, y = y)
        return label

    def button(self, root, x, y, w, var = None, text = None):

        """ Create a new button
        :param root: Parent window
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param w: Width of the button
        :param var: StringVar as the button title (it can be changed later)
        :param text: String as the button title
        """

        button = None

        if(var is not None):
            button = Tkinter.Button(root, textvariable = var, width = w)
        elif(text is not None):
            button = Tkinter.Button(root, text = text, width = w)

        button.place(x = x, y = y)
        return button

    def menu(self, root, x, y, w, var, values):

        """ Create a new menu
        :param root: Parent window
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param w: Width of the menu
        :param var: StringVar for storing the current value
        :param values: List of possible values
        """

        menu = apply(Tkinter.OptionMenu, (root, var) + tuple(values))
        menu.config(width = w)
        menu.place(x = x, y = y)
        return menu

    def check(self, root, x, y, var, on, off):

        """ Create a new checkbox
        :param root: Parent window
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param var: StringVar which storing the value
        :param on: Value of the checkbox, if it is checked
        :param off: Value of the checkbox if it is not checked
        """

        check = Tkinter.Checkbutton(root, variable = var, offvalue = off, onvalue = on)
        check.place(x = x, y = y)
        return check


class Config(ElementTree):
    name = None

    def __init__(self, name):

        """ Open an XML file
        :param name: Name of the XML file
        """

        ElementTree.__init__(self, file = name)
        self.name = name

    def __setitem__(self, key, value):

        """ Set an item
        :param key: Name of the item
        :param value: Value of the item
        """

        if value is not None:
            self._root.find(key).text = unicode(value)
        else:
            self._root.find(key).text = None

    def __getitem__(self, key):

        """ Get an item
        :param key: Name of the item
        """

        try:
            if int(self._root.find(key).text) == float(self._root.find(key).text):
                return int(self._root.find(key).text)
            else:
                return float(self._root.find(key).text)
        except (ValueError, TypeError):
            return self._root.find(key).text

    def save(self):

        """ Save the opened XML file """

        self.write(self.name)


class Notification(Tkinter.Toplevel, Window):
    def __init__(self, parent, message, timeout = 1500):

        """ Initializing a notification window
        :param parent: The parent window
        :param message: Message which will show in the notification
        :param timeout: Timeout of the notification
        """

        Tkinter.Toplevel.__init__(self, parent, bg = 'white')

        self.overrideredirect(1)
        self.geometry("%dx%d%+d%+d" % (128, 24, self.winfo_screenwidth() - 128, 0))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-alpha', 0.65)
        self.wm_attributes("-topmost", 1)

        self.bind("<Button-1>", lambda event: self.quit())
        self.after(timeout, self.quit)

        message = self.label(self, 5, 0, message)
        message.config(bg = "white", fg = "black")


class SettingsWindow(Tkinter.Toplevel, Window):
    config = None

    def __init__(self, parent, session, config, status = Reference(False)):

        """ Initializing the settings window
        :param parent: The parent window
        :param session: Current session
        :param status: Status of the parent window
        """

        Tkinter.Toplevel.__init__(self, parent, width = 175, height = 175)
        self.config = config

        self.protocol('WM_DELETE_WINDOW', lambda: self.deleteEvent(status))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-toolwindow', 1)
        self.wm_attributes("-topmost", 1)
        self.title(u"Settings")
        self.wm_iconbitmap(ICON)
        self.geometry('%dx%d+%d+%d' % (175, 175, self.winfo_screenwidth() / 2 - 87,
                                       self.winfo_screenheight() / 2 - 87))

        # Create the automatic URL copy checkbox

        self.label(self, 5, 5, "Automatic URL copy:")

        copyValue = Tkinter.StringVar()
        copyCheck = self.check(self, 150, 5, copyValue, 'true', 'false')
        copyValue.trace(callback = lambda varName, elementName, mode: self.set('copy', copyValue), mode = 'w')

        if self.config['copy'] == 'false':
            copyCheck.deselect()

        # Create the browser behavior checkbox

        self.label(self, 5, 30, "Open in the browser:")

        browserValue = Tkinter.StringVar()
        browserCheck = self.check(self, 150, 30, browserValue, 'true', 'false')
        browserValue.trace(callback = lambda varName, elementName, mode: self.set('browser', browserValue), mode = 'w')

        if self.config['browser'] == 'false':
            browserCheck.deselect()

        # Create the notification behavior checkbox

        self.label(self, 5, 55, "Show notification:")

        notificationValue = Tkinter.StringVar()
        notificationCheck = self.check(self, 150, 55, notificationValue, 'true', 'false')
        notificationValue.trace(callback = lambda varName, elementName, mode: self.set('notification',
                                                                                       notificationValue), mode = 'w')

        if self.config['notification'] == 'false':
            notificationCheck.deselect()

        # Create the direct link activator checkbox

        self.label(self, 5, 80, "Use direct link:")

        shortValue = Tkinter.StringVar()
        shortCheck = self.check(self, 150, 80, shortValue, 'true', 'false')
        shortValue.trace(callback = lambda varName, elementName, mode: self.set('direct', shortValue), mode = 'w')

        if self.config['direct'] == 'false':
            shortCheck.deselect()

        # Create the server list

        serverValue = Tkinter.StringVar()
        serverValue.set(self.config['server'])
        serverValue.trace(callback = lambda varName, elementName, mode: self.set('server', serverValue), mode = 'w')

        self.menu(self, 6, 105, 20, serverValue, SERVERS)

        # Create the unlink button

        button = self.button(self, 5, 140, 22, text = "Unlink client")
        button.bind("<Button-1>", lambda event: self.unlink(parent, session))

        status.set(True)
        self.focus()

    def deleteEvent(self, status):

        """ Settings window closing function
        :param status: Status of the settings window
        """

        status.set(False)
        self.destroy()

    def set(self, key, value):

        """ Set a parameter
        :param key: Name of the parameter
        :param value: Value of the parameter
        """

        if str(value):
            self.config[key] = value.get()

    def unlink(self, parent, session):

        """ Unlink client from the server, and close every window
        :param parent: Parent window
        :param session: Status of the settings window
        """

        session.unlink()
        parent.deleteEvent()


class GrabWindow(Tkinter.Tk):
    disabled = Reference(False)
    session = None
    config = None
    square = None
    last = False
    x, y, = 0, 0

    def __init__(self):

        """ Initializing the grab window """

        Tkinter.Tk.__init__(self)
        self.config = Config(CONFIG)

        self.protocol('WM_DELETE_WINDOW', self.deleteEvent)
        self.configure(background = 'white')
        self.wm_attributes("-topmost", 1)
        self.attributes('-fullscreen', 1)
        self.attributes('-alpha', 0.2)
        self.wm_iconbitmap(ICON)
        self.title(u"JamCrop")

        self.bind("<Button-1>", self.click)
        self.bind_all('<Key>', self.keyPress)
        self.square = Tkinter.Canvas(self, width = 0, height = 0, bg = 'blue', bd = 0)

        self.withdraw()
        self.session = Connection(self.config)

        if not self.session.load():
            request_token = self.session.authorize()
            webbrowser.open("%s?%s" % ("https://www.dropbox.com/1/oauth/authorize",
                            urllib.urlencode({'oauth_token': request_token['oauth_token']})))

            if tkMessageBox.askokcancel(title = "JamCrop", message = "The JamCrop requires a limited Dropbox "
                                                                     "access for itself. If you allowed the "
                                                                     "connection to your Dropbox, from the recently "
                                                                     "appeared browser window, please click on the "
                                                                     "OK button. After the grab window has appeared, "
                                                                     "you can open settings by pressing [F1]."):
                self.session.access()
            else:
                self.deleteEvent()

        self.update()
        self.deiconify()

    def deleteEvent(self):

        """ Closing function for the grab window """

        self.config.save()
        self.destroy()
        sys.exit()

    def autoFocus(self):

        """ Automatic focus for the grab window """

        if self.disabled.get():
            self.wm_attributes("-topmost", 0)
        else:
            self.wm_attributes("-topmost", 1)
            self.tkraise()
            self.focus()
        self.after(250, self.autoFocus)

    def keyPress(self, event):

        """ Track the key presses
        :param event: The event which started the function
        """

        if event.keysym == 'Escape':
            self.deleteEvent()
        elif event.keysym == 'F1' and not self.disabled.get():
            config = SettingsWindow(self, self.session, self.config, self.disabled)
            config.mainloop()

    def drawSquare(self, event):

        """ Draw the selecting square on to the grab window
        :param event: The event which started the function
        """

        if self.x < event.x_root and self.y < event.y_root:
            self.square.config(width = event.x_root - self.x, height = event.y_root - self.y)
            self.square.place(x = self.x, y = self.y)
        elif self.x > event.x_root and self.y > event.y_root:
            self.square.config(width = self.x - event.x_root, height = self.y - event.y_root)
            self.square.place(x = event.x_root, y = event.y_root)
        elif self.x < event.x_root and self.y > event.y_root:
            self.square.config(width = event.x_root - self.x, height = self.y - event.y_root)
            self.square.place(x = self.x, y = event.y_root)
        elif self.x > event.x_root and self.y < event.y_root:
            self.square.config(width = self.x - event.x_root, height = event.y_root - self.y)
            self.square.place(x = event.x_root, y = self.y)
        else:
            self.square.place_forget()

    def click(self, event):

        """ Set the coordinates of the screenshot
        :param event: The event which started the function
        """

        if not self.disabled.get() and not self.last:
            self.bind("<Motion>", self.drawSquare)
            self.bind("<ButtonRelease-1>", self.click)
            self.x = event.x_root
            self.y = event.y_root
            self.last = True
        elif not self.disabled.get():
            if self.x < event.x_root and self.y < event.y_root:
                self.grab(self.x, self.y, event.x_root, event.y_root)
            elif self.x > event.x_root and self.y > event.y_root:
                self.grab(event.x_root, event.y_root, self.x, self.y)
            elif self.x < event.x_root and self.y > event.y_root:
                self.grab(self.x, event.y_root, event.x_root, self.y)
            elif self.x > event.x_root and self.y < event.y_root:
                self.grab(event.x_root, self.y, self.x, event.y_root)
            else:
                self.grab(0, 0, self.winfo_screenwidth(), self.winfo_screenheight())

    def grab(self, x, y, w, h):

        """ Create the screenshot from the coordinates
        :param x: First horizontal pixel of the image
        :param y: First vertical pixel of the image
        :param w: Width of the image (in pixels)
        :param h: Height of the image
        """

        self.withdraw()

        fileName = "%s.jpg" % str(time.strftime('%Y_%m_%d_%H_%M_%S'))
        ImageGrab.grab((x, y, w, h)).save(fileName)

        try:
            self.session.upload(fileName)
        except:
            self.deleteEvent()
        finally:
            os.unlink(fileName)

        if self.config['direct'] == 'true':
            result = self.session.share(fileName, 'false')
            result['url'] += '?dl=1'
        else:
            result = self.session.share(fileName, 'true')

        if self.config['copy'] == 'true':
            self.clipboard_clear()
            self.clipboard_append(result['url'])

        if self.config['browser'] == 'true':
            webbrowser.open(result['url'])

        if self.config['notification'] == 'true':
            alert = Notification(self, "Uploading is completed", TIMEOUT)
            alert.geometry("%dx%d%+d%+d" % (140, 23, self.winfo_screenwidth() - 140, 0))
            alert.mainloop()

        self.deleteEvent()


def main():
    crop = GrabWindow()
    crop.autoFocus()
    crop.mainloop()


if __name__ == '__main__':
    main()