#!/usr/bin/env python
#-*- coding: utf-8 -*-

__author__ = "Tornyi Dénes"
__version__ = "1.0.0"


SERVER = 'jamcropxy.appspot.com'
CONFIG = 'config.xml'
ICON = 'icon.ico'


from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from xml.etree.ElementTree import ElementTree
from PyQt4 import QtGui, QtCore
from pil import ImageGrab
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

        result = urllib2.urlopen('https://%s/authorize' % SERVER)
        self.request_token = dict(urlparse.parse_qsl(result.read()))
        return self.request_token

    def access(self):

        """ Get an access token with the request token """

        result = urllib2.urlopen('%s?%s' % ('https://%s/access' % SERVER, urllib.urlencode(self.request_token)))
        self.access_token = dict(urlparse.parse_qsl(result.read()))
        self.config['token'] = urllib.urlencode(self.access_token)
        return self.access_token

    def load(self):

        """ Load the previously saved access token """

        if self.config['token'] is not None:
            self.access_token = dict(urlparse.parse_qsl(self.config['token']))
            return True
        else: return False

    def unlink(self):

        """ Delete token from the config """

        self.config['token'] = None

    def upload(self, fileName):

        """ Upload a file to the server
        :param fileName: Name of the file for upload
        """

        body, headers = multipart_encode({'body': open(fileName, 'rb')})
        request = urllib2.Request('%s?%s' % ('https://%s/upload' % SERVER,
                                             urllib.urlencode(dict(self.access_token.items() +
                                                                   dict({'name': fileName}).items()))), body, headers)
        return json.loads(urllib2.urlopen(request).read())

    def share(self, fileName, short = 'false'):

        """ Get the link of an uploaded file
        :param fileName: Name of the file for share
        :param short: Get short or long URL
        """

        request = urllib2.Request('%s?%s' % ('https://%s/share' % SERVER,
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

        """ Set an item of the file
        :param key: Name of the item
        :param value: Value of the item
        """

        self._root.find(key).text = value

    def __getitem__(self, key):

        """ Get an item of the file
        :param key: Name of the item
        """

        return self._root.find(key).text

    def save(self):

        """ Save the opened XML file """

        self.write(self.name)


class SettingsWindow(Tkinter.Toplevel, Window):
    config = None

    def __init__(self, parent, session, config, status = Reference(False)):

        """ Initializing the settings window
        :param parent: The parent window
        :param session: Current session
        :param status: Status of the parent window
        """

        Tkinter.Toplevel.__init__(self, parent, width = 195, height = 160)
        self.config = config

        self.protocol('WM_DELETE_WINDOW', lambda: self.deleteEvent(status))
        self.resizable(width = 'false', height = 'false')
        self.attributes('-toolwindow', 1)
        self.wm_attributes("-topmost", 1)
        self.title(u"Settings")
        self.wm_iconbitmap(ICON)

        # Create the automatic URL copy checkbox

        self.label(self, 5, 5, "Automatic URL copy:")

        copyValue = Tkinter.StringVar()
        copyCheck = self.check(self, 172, 5, copyValue, 'true', 'false')
        copyValue.trace(callback = lambda varName, elementName, mode: self.setConfig('copy', copyValue),
                        mode = 'w')

        if self.config['copy'] == 'false':
            copyCheck.deselect()

        # Create the browser behavior checkbox

        self.label(self, 5, 30, "Open in the browser:")

        browserValue = Tkinter.StringVar()
        browserCheck = self.check(self, 172, 30, browserValue, 'true', 'false')
        browserValue.trace(callback = lambda varName, elementName, mode: self.setConfig('browser', browserValue),
                           mode = 'w')

        if self.config['browser'] == 'false':
            browserCheck.deselect()

        # Create the tooltip behavior checkbox

        self.label(self, 5, 55, "Show a tooltip:")

        tooltipValue = Tkinter.StringVar()
        tooltipCheck = self.check(self, 172, 55, tooltipValue, 'true', 'false')
        tooltipValue.trace(callback = lambda varName, elementName, mode: self.setConfig('tooltip', tooltipValue),
                           mode = 'w')

        if self.config['tooltip'] == 'false':
            tooltipCheck.deselect()

        # Create the direct link activator checkbox

        self.label(self, 5, 80, "Use direct link:")

        shortValue = Tkinter.StringVar()
        shortCheck = self.check(self, 172, 80, shortValue, 'false', 'true')
        shortValue.trace(callback = lambda varName, elementName, mode: self.setConfig('short', shortValue),
                         mode = 'w')

        if self.config['short'] == 'true':
            shortCheck.deselect()

        # Create the list of image formats

        self.label(self, 5, 105, "Image format:")

        formatValue = Tkinter.StringVar()
        formatValue.set(self.config['format'])
        formatValue.trace(callback = lambda varName, elementName, mode: self.setConfig('format', formatValue),
                          mode = 'w')

        self.menu(self, 93, 100, 9, formatValue, ['jpg', 'png', 'gif'])

        # Create the button to unlink the client

        button = self.button(self, 5, 130, 25, text = "Unlink client")
        button.bind("<Button-1>", lambda event: self.unlink(parent, session))

        status.set(True)

    def deleteEvent(self, status):

        """ Settings window closing function
        :param status: Status of the settings window
        """

        status.set(False)
        self.destroy()

    def setConfig(self, key, value):

        """ Set a parameter
        :param key: Name of the parameter
        :param value: Value of the parameter
        """

        self.config[key] = unicode(value.get())

    def unlink(self, parent, session):

        """ Unlink client from the server, and close every window
        :param parent: Parent window
        :param session: Status of the settings window
        """

        session.unlink()
        parent.deleteEvent()


class GrabWindow(QtGui.QWidget):
    disabled = Reference(False)
    settings = None
    config = None
    shape = None

    def __init__(self):
        super(GrabWindow, self).__init__()
        self.config = Config(CONFIG)

        self.screen = QtGui.QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, self.screen.width(), self.screen.height())

        self.setWindowTitle('JamCrop')
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.shape = QtGui.QRubberBand(QtGui.QRubberBand.Rectangle, self)
        self.setMouseTracking(True)

        self.session = Connection(self.config)

        if(not self.session.load()):
            request_token = self.session.authorize()
            webbrowser.open("%s?%s" % ("https://www.dropbox.com/1/oauth/authorize",
                                       urllib.urlencode({'oauth_token' : request_token['oauth_token']})))

            reply = QtGui.QMessageBox.question(self, 'JamCrop', "The JamCrop require a limited Dropbox"
                                                                " access for itself. If you allowed the "
                                                                "connection to the Dropbox, from the recently "
                                                                "appeared browser window, please click on the "
                                                                "OK button. After the grab window have appeared, "
                                                                "you can open settings by pressing [F1].",
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                self.session.access()
            else: return

        self.activateWindow()
        self.show()

    def paintEvent(self, event):
        canvas = QtGui.QPainter()
        canvas.begin(self)
        canvas.setPen(QtGui.QColor(0, 0, 0, 1))
        canvas.setBrush(QtGui.QColor(0, 0, 0, 1))
        canvas.drawRect(0, 0, self.screen.width(), self.screen.height())
        canvas.end()

    def closeEvent(self, event):
        self.config.save()
        self.close()
        sys.exit()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F1:
            self.settings = SettingsWindow(self.disabled)
            self.settings.activateWindow()
            print("Settings...")
        elif event.key() == QtCore.Qt.Key_Escape:
            self.close()
            sys.exit()

    def mousePressEvent(self, event):
        if not self.disabled.get():
            self.origin = event.pos()
            self.shape.setGeometry(QtCore.QRect(self.origin, QtCore.QSize()))
            self.shape.show()
            QtGui.QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if not self.disabled.get():
            if self.shape.isVisible():
                self.shape.setGeometry(QtCore.QRect(self.origin, event.pos()).normalized())
            QtGui.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if not self.disabled.get():
            if self.shape.isVisible():
                self.shape.hide()
                self.hide()

                fileName = "%s.%s" % (str(time.strftime('%Y_%m_%d_%H_%M_%S')), str(self.config['format']))

                shot = QtGui.QPixmap.grabWindow(QtGui.QApplication.desktop().winId()).copy(self.shape.geometry())
                shot.save(fileName, str(self.config['format']))

                self.session.upload(fileName)
                os.unlink(fileName)

                result = self.session.share(fileName, self.config['short'])

                if self.config['short'] == 'false':
                    result['url'] += '?dl=1'

                if self.config['copy'] == 'true':
                    self.clipboard_clear()
                    self.clipboard_append(result['url'])

                if self.config['browser'] == 'true':
                    webbrowser.open(result['url'])

                if self.config['tooltip'] == 'true':
                    print("Uploading is completed")

                self.close()
                sys.exit()
            QtGui.QWidget.mouseReleaseEvent(self, event)
            self.activateWindow()


def main():
    app = QtGui.QApplication(sys.argv)
    crop = GrabWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()