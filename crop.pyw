#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-


__author__ = ["Dénes Tornyi"]
__version__ = "1.2.0"


PROTOCOL = 'https'
SERVERS = ['jamcropxy.appspot.com']
FORMATS = ['jpg', 'png']
TIMEOUT = 2500
CONFIG = 'config.xml'
ICON = 'icon.ico'


from poster.streaminghttp import register_openers
from xml.etree.ElementTree import ElementTree
from poster.encode import multipart_encode
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

        result = urllib2.urlopen('%s://%s/authorize' % (PROTOCOL, self.config['server']))
        self.request_token = dict(urlparse.parse_qsl(result.read()))
        return self.request_token

    def access(self):

        """ Get an access token with the request token """

        result = urllib2.urlopen('%s?%s' % ('%s://%s/access' % (PROTOCOL, self.config['server']),
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
        request = urllib2.Request('%s?%s' % ('%s://%s/upload' % (PROTOCOL, self.config['server']),
                                             urllib.urlencode(dict(self.access_token.items() +
                                                                   dict({'name': fileName}).items()))), body, headers)
        return json.loads(urllib2.urlopen(request).read())

    def share(self, fileName, short = 'false'):

        """ Get the link of an uploaded file
        :param fileName: Name of the file for share
        :param short: Get short or long URL
        """

        request = urllib2.Request('%s?%s' % ('%s://%s/share' % (PROTOCOL, self.config['server']),
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

        Tkinter.Toplevel.__init__(self, parent)
        self.config = config

        self.geometry('%dx%d+%d+%d' % (162, 205, self.winfo_screenwidth() / 2 - 81,
                                       self.winfo_screenheight() / 2 - 102))
        self.protocol('WM_DELETE_WINDOW', lambda: self.deleteEvent(status))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-toolwindow', 1)
        self.wm_attributes("-topmost", 1)
        self.title(u"Settings")
        self.wm_iconbitmap(ICON)

        # Create the automatic URL copy checkbox

        copyValue = Tkinter.StringVar()
        copyCheck = self.check(self, 5, 5, copyValue, 'true', 'false')
        copyValue.trace(callback = lambda varName, elementName, mode: self.set('copy', copyValue), mode = 'w')

        if self.config['copy'] == 'false':
            copyCheck.deselect()

        self.label(self, 25, 7, "Automatic URL copy")

        # Create the browser behavior checkbox

        browserValue = Tkinter.StringVar()
        browserCheck = self.check(self, 5, 30, browserValue, 'true', 'false')
        browserValue.trace(callback = lambda varName, elementName, mode: self.set('browser', browserValue), mode = 'w')

        if self.config['browser'] == 'false':
            browserCheck.deselect()

        self.label(self, 25, 32, "Open in the browser")

        # Create the notification behavior checkbox

        notificationValue = Tkinter.StringVar()
        notificationCheck = self.check(self, 5, 55, notificationValue, 'true', 'false')
        notificationValue.trace(callback = lambda varName, elementName, mode: self.set('notification',
                                                                                       notificationValue), mode = 'w')

        if self.config['notification'] == 'false':
            notificationCheck.deselect()

        self.label(self, 25, 57, "Show notification")

        # Create the direct link activator checkbox

        shortValue = Tkinter.StringVar()
        shortCheck = self.check(self, 5, 80, shortValue, 'true', 'false')
        shortValue.trace(callback = lambda varName, elementName, mode: self.set('direct', shortValue), mode = 'w')

        if self.config['direct'] == 'false':
            shortCheck.deselect()

        self.label(self, 25, 82, "Use direct link")

        # Create the format list

        formatValue = Tkinter.StringVar()
        formatValue.set(self.config['format'])
        formatValue.trace(callback = lambda varName, elementName, mode: self.set('format', formatValue), mode = 'w')

        self.menu(self, 6, 105, 18, formatValue, FORMATS)

        # Create the server list

        serverValue = Tkinter.StringVar()
        serverValue.set(self.config['server'])
        serverValue.trace(callback = lambda varName, elementName, mode: self.set('server', serverValue), mode = 'w')

        self.menu(self, 6, 135, 18, serverValue, SERVERS)

        # Create the unlink button

        button = self.button(self, 7, 170, 20, text = "Unlink client")
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
    last = False
    rect = None
    x, y, = 0, 0

    def __init__(self):

        """ Initializing the grab window """

        Tkinter.Tk.__init__(self)
        self.config = Config(CONFIG)

        self.protocol('WM_DELETE_WINDOW', self.deleteEvent)
        self.configure(background = 'black')
        self.wm_attributes("-topmost", 1)
        self.attributes('-fullscreen', 1)
        self.attributes('-alpha', 0.01)
        self.wm_iconbitmap(ICON)
        self.title(u"JamCrop")

        self.bind("<Button-1>", self.click)
        self.bind_all('<Key>', self.keyPress)

        self.withdraw()
        self.session = Connection(self.config)

        if not self.session.load():
            request_token = self.session.authorize()
            webbrowser.open("%s%s?%s" % (PROTOCOL, "://www.dropbox.com/1/oauth/authorize",
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

    def initRectangle(self, event):

        """ Init the selecting rectangle (which is a window) on to the grab window
        :param event: The event which started the function
        """

        self.rect = Tkinter.Toplevel()
        self.rect.resizable(width = 'false', height = 'false')
        self.attributes('-toolwindow', 1)
        self.rect.configure(background = '#00a2ff')
        self.rect.wm_attributes("-topmost", 1)
        self.rect.attributes('-alpha', 0.20)
        self.rect.overrideredirect(1)
        self.bind("<Motion>", self.drawRectangle)
        self.rect.bind("<Motion>", self.drawRectangle)
        self.rect.mainloop()

    def drawRectangle(self, event):

        """ Draw the selecting rectangle on to the grab window
        :param event: The event which started the function
        """

        if self.x < event.x_root and self.y < event.y_root:
            self.rect.geometry("%dx%d%+d%+d" % (event.x_root - self.x, event.y_root - self.y, self.x, self.y))
        elif self.x > event.x_root and self.y > event.y_root:
            self.rect.geometry("%dx%d%+d%+d" % (self.x - event.x_root, self.y - event.y_root, event.x_root, event.y_root))
        elif self.x < event.x_root and self.y > event.y_root:
            self.rect.geometry("%dx%d%+d%+d" % (event.x_root - self.x, self.y - event.y_root, self.x, event.y_root))
        elif self.x > event.x_root and self.y < event.y_root:
            self.rect.geometry("%dx%d%+d%+d" % (self.x - event.x_root, event.y_root - self.y, event.x_root, self.y))
        self.focus()

    def click(self, event):

        """ Set the coordinates of the screenshot
        :param event: The event which started the function
        """


        if not self.disabled.get() and not self.last:
            self.bind("<ButtonRelease-1>", self.click)
            self.bind("<Motion>", self.initRectangle)
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

    def hide(self):

        """ Hide the grab window, with the selecting rectangle """

        try:
            self.withdraw()
            self.rect.destroy()
        except AttributeError:
            self.withdraw()

    def grab(self, x, y, w, h):

        """ Create the screenshot from the coordinates
        :param x: First horizontal pixel of the image
        :param y: First vertical pixel of the image
        :param w: Width of the image (in pixels)
        :param h: Height of the image
        """

        self.hide()
        fileName = "%s.%s" % (str(time.strftime('%Y_%m_%d_%H_%M_%S')), self.config['format'])
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