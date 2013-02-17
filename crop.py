#!/usr/bin/env python
#-*- coding: utf-8 -*-


SERVER = 'jamcropxy.appspot.com'
CONFIG = 'config.xml'
ICON = 'icon.ico'


from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
import xml.etree.ElementTree as xml
from pil import ImageGrab
import tkMessageBox
import webbrowser
import urlparse
import Tkinter
import urllib2
import urllib
import json
import time
import os


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


class server():
    request_token = None
    access_token = None

    def authorize(self):

        """ Get a request token from the server """

        result = urllib2.urlopen('https://%s/authorize' % SERVER)
        self.request_token = dict(urlparse.parse_qsl(result.read()))
        return self.request_token

    def access(self):

        """ Get an access token with the request token """

        result = urllib2.urlopen('%s?%s' % ('https://%s/access' % SERVER, urllib.urlencode(self.request_token)))
        self.access_token = dict(urlparse.parse_qsl(result.read()))
        config.getroot().find('token').text = urllib.urlencode(self.access_token)
        return self.access_token

    def load(self):

        """ Load the previously saved access token """

        if config.getroot().find('token').text is not None:
            self.access_token = dict(urlparse.parse_qsl(config.getroot().find('token').text))
            return 1
        else:
            return 0

    def unlink(self):

        """ Delete every token from the memory and from the config """

        config.getroot().find('token').text = None
        self.request_token = None
        self.access_token = None

    def upload(self, fileName):

        """ Upload a file to the server
        :param fileName: Name of the file for upload
        """

        body, headers = multipart_encode({'body': open(fileName, 'rb')})
        request = urllib2.Request('%s?%s' % ('https://%s/upload' % SERVER,
                                             urllib.urlencode(dict(self.access_token.items() +
                                                                   dict({'name': fileName}).items()))), body, headers)
        return json.loads(urllib2.urlopen(request).read())

    def share(self, fileName, shortUrl = 'false'):

        """ Get a link of the previously uploaded file
        :param fileName: Name of the file for share
        :param shortUrl: Get short or long URL
        """

        request = urllib2.Request('%s?%s' % ('https://%s/share' % SERVER,
                                  urllib.urlencode(dict(self.access_token.items() +
                                                        dict({'name': fileName, 'short': shortUrl}).items()))))
        return json.loads((urllib2.urlopen(request)).read())


class window():
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

        if(var != None):
            button = Tkinter.Button(root, textvariable = var, width = w)
        elif(text != None):
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
        :param values: A list of possible values
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


class tooltip(Tkinter.Toplevel, window):
    def __init__(self, parent, message, timeout = 1500):

        """ Initializing a tooltip window
        :param parent: The parent window
        :param message: Message which will show in the tooltip
        :param timeout: Timeout of the tooltip
        """

        Tkinter.Toplevel.__init__(self, parent, bg = 'white')

        self.overrideredirect(1)
        self.geometry("%dx%d%+d%+d" % (128, 24, self.winfo_screenwidth() - 128, 0))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-alpha', 0.65)
        self.wm_attributes("-topmost", 1)

        self.bind("<Button-1>", lambda event: self.destroy())
        self.after(timeout, self.destroy)

        message = self.label(self, 5, 0, message)
        message.config(bg = "white", fg = "black")


class configWindow(Tkinter.Toplevel, window):
    def __init__(self, parent, session, status = reference(0)):

        """ Initializing the config window
        :param parent: The parent window
        :param session: Current session
        :param status: Status of the config window
        """

        Tkinter.Toplevel.__init__(self, parent, width = 195, height = 135)

        self.protocol('WM_DELETE_WINDOW', lambda: self.deleteEvent(status))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-toolwindow', 1)
        self.wm_attributes("-topmost", 1)
        self.title(u"Configuration")
        self.wm_iconbitmap(ICON)

        # Create the automatic URL copy checkbox

        self.label(self, 5, 5, "Automatic URL copy:")

        copyValue = Tkinter.StringVar()
        copyCheck = self.check(self, 172, 5, copyValue, 'true', 'false')
        copyValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setConfig('copy', copyValue))

        if config.getroot().find('copy').text == 'false':
            copyCheck.deselect()

        # Create the browser behavior checkbox

        self.label(self, 5, 30, "Open in the browser:")

        shortValue = Tkinter.StringVar()
        shortCheck = self.check(self, 172, 30, shortValue, 'true', 'false')
        shortValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setConfig('browser', shortValue))

        if config.getroot().find('browser').text == 'false':
            shortCheck.deselect()

        # Create the tooltip checkbox

        self.label(self, 5, 55, "Show a tooltip:")

        tooltipValue = Tkinter.StringVar()
        tooltipCheck = self.check(self, 172, 55, tooltipValue, 'true', 'false')
        tooltipValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setConfig('tooltip', tooltipValue))

        if config.getroot().find('tooltip').text == 'false':
            tooltipCheck.deselect()

        # Create the list of image formats

        self.label(self, 5, 80, "Image format:")

        formatValue = Tkinter.StringVar()
        formatValue.set(config.getroot().find('format').text)
        formatValue.trace(mode = 'w', callback = lambda varName, elementName, mode: self.setConfig('format', formatValue))
        self.menu(self, 93, 75, 9, formatValue, ['jpg', 'png', 'gif'])

        # Create the button to unlink the client

        button = self.button(self, 5, 105, 25, text = "Unlink client")
        button.bind("<Button-1>", lambda event: self.doUnlink(parent, session))

        status.set(1)

    def deleteEvent(self, status):

        """ Configuration window closing function
        :param status: Status of the config window
        """

        status.set(0)
        self.destroy()

    def setConfig(self, key, value):

        """ Set the url copy parameter
        :param key: Name of the parameter
        :param value: Value of the paramter
        """

        config.getroot().find(key).text = unicode(value.get())

    def doUnlink(self, parent, session):

        """ Unlink JamCrop from the server, and close every window
        :param parent: Parent window
        :param session: Status of the config window
        """

        session.unlink()
        parent.deleteEvent()


class grabWindow(Tkinter.Tk):
    disabled = reference(0)
    x, y, last = 0, 0, 0
    session = None
    square = None

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
        self.session = server()

        if(not self.session.load()):
            request_token = self.session.authorize()
            webbrowser.open("%s?%s" % ("https://www.dropbox.com/1/oauth/authorize",
                            urllib.urlencode({'oauth_token' : request_token['oauth_token']})))

            if tkMessageBox.askokcancel(title = "JamCrop", message = "The JamCrop require a limited Dropbox"
                                                                     " access for itself. If you allowed the "
                                                                     "connection to the Dropbox, from the recently "
                                                                     "appeared browser window, please click on the "
                                                                     "OK button. After the grab window have shown, "
                                                                     "you can open the configuration window by "
                                                                     "pressing the F1 button."): self.session.access()
            else: return

        self.update()
        self.deiconify()

    def deleteEvent(self):

        """ Closing function for the grab window """

        config.write(CONFIG)
        self.destroy()

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
            config = configWindow(self, self.session, self.disabled)
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

        if(not self.disabled.get() and not self.last):
            self.bind("<Motion>", self.drawSquare)
            self.x = event.x_root
            self.y = event.y_root
            self.last = 1
        elif(not self.disabled.get()):
            if self.x < event.x_root and self.y < event.y_root:
                self.grab(self.x, self.y, event.x_root, event.y_root)
            elif self.x > event.x_root and self.y > event.y_root:
                self.grab(event.x_root, event.y_root, self.x, self.y)
            elif self.x < event.x_root and self.y > event.y_root:
                self.grab(self.x, event.y_root, event.x_root, self.y)
            elif self.x > event.x_root and self.y < event.y_root:
                self.grab(event.x_root, self.y, self.x, event.y_root)
            else:
                self.unbind("<Motion>")
                self.square.place_forget()
                self.last = 0

    def grab(self, x, y, w, h):

        """ Create the screenshot from the coordinates
        :param x: First horizontal pixel of the image
        :param y: First vertical pixel of the image
        :param w: Width of the image (in pixels)
        :param h: Height of the image
        """

        self.withdraw()

        fileName = "%s.%s" % (str(time.strftime('%Y_%m_%d_%H_%M_%S')), str(config.getroot().find('format').text))

        ImageGrab.grab((x, y, w, h)).save(fileName)
        self.session.upload(fileName)
        os.unlink(fileName)

        result = self.session.share(fileName, 'true')

        if config.getroot().find('copy').text == 'true':
            self.clipboard_clear()
            self.clipboard_append(result['url'])

        if config.getroot().find('browser').text == 'true':
            webbrowser.open(result['url'])

        if config.getroot().find('tooltip').text == 'true':
            alert = tooltip(self, "Uploading is completed", 2500)
            alert.geometry("%dx%d%+d%+d" % (140, 23, self.winfo_screenwidth() - 140, 0))
            alert.mainloop()

        self.deleteEvent()


def main():
    crop = grabWindow()
    crop.autoFocus()
    crop.mainloop()


if __name__ == '__main__':
    config = xml.parse(CONFIG)
    main()