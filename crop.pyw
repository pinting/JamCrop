#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""JamCrop.py: This is a client for uploading files into several
image hosting servers. Dropbox included."""

from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import webbrowser
import pyperclip
import urlparse
import urllib2
import urllib
import json
import time
import sys
import os

__author__      = "Dénes Tornyi, Ádam Tajti"
__version__     = "2.0.2"


SERVERS = ['jamcropxy.appspot.com', 'jamcropxy-pinting.rhcloud.com']
CONFIG = 'config.json'
ICON = 'icon.ico'
TIMEOUT = 2.0

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

        result = urllib2.urlopen('%s?%s' % ('https://%s/access' %  self.config['server'],
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


class Config:
    config = None
    fileName = None

    def __init__(self, fileName):

        """ Open an XML file
        :param fileName: Name of the json config file
        """

        self.fileName = fileName
        with open(self.fileName, 'r') as config_file:
            self.config = json.load(config_file)

    def __setitem__(self, key, value):
        self.config[key] = value

    def __getitem__(self, key):
        try:
            return self.config[key]
        except:
            pass


    def save(self):
        with open(self.fileName, 'w') as config_file:
            json.dump(self.config, config_file, indent=4)


class Window(QWidget):
    def center(self):

        """ Move the window to the center """

        frame = self.frameGeometry()
        screen = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    def label(self, msg, x, y):

        """ Create a new label
        :param msg: Content of the label
        :param x: First horizontal pixel
        :param y: First vertical pixel
        """

        label = QLabel(msg, self)
        label.move(x, y)
        return label

    def button(self, title, x, y, onclick = False):

        """ Create a new button
        :param title: Title of the button
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param onclick: A function for processing the results
        """

        button = QPushButton(title, self)
        button.resize(button.sizeHint())
        button.move(x, y)

        if onclick:
            button.clicked.connect(onclick)

        return button

    def field(self, x, y, w, h, default = False, action = False):

        """ Create a new field
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param w: Width of the field
        :param h: Height of the field
        :param default: Default value
        :param action: A function for processing the changes
        """

        field = QLineEdit(self)
        field.setMaxLength(64)
        field.move(x, y)
        field.resize(w, h)

        if default:
            field.setText(default)
        if action:
            field.textEdited.connect(action)

        return field

    def check(self, desc, x, y, action = False):

        """ Create a new checkbox
        :param desc: The description of the checkbox
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param action: A function for processing the results
        """

        check = QCheckBox(desc, self)
        check.move(x, y)

        if action:
            check.stateChanged.connect(action)

        return check

    def combo(self, x, y, values, action = False):

        """ Create a new list
        :param values: List of possible values
        :param x: First horizontal pixel
        :param y: First vertical pixel
        :param action: A function for processing the results
        """

        combo = QComboBox(self)
        combo.setEditable(True)
        combo.addItems(values)
        combo.move(x, y)

        if action:
            combo.editTextChanged.connect(action)

        return combo


class Notification(QSystemTrayIcon):
    def __init__(self, title, msg, icon, parent = None):

        """ Initializing a notification
        :param title: Title of the notification
        :param msg: Message of the notification
        :param icon: Icon of the application on the system tray
        :param parent: The parent window
        """

        QSystemTrayIcon.__init__(self, parent)
        self.setIcon(QIcon(icon))
        self.show()
        self.showMessage(title, msg)


class SettingsWindow(Window):
    session = None
    config = None
    status = None

    def __init__(self, parent, session, config, status = Reference(False)):

        """ Initializing the settings window
        :param parent: The parent window
        :param session: Current session
        :param config: Current config
        :param status: Status of the parent window
        """

        Window.__init__(self)
        self.config = config
        self.status = status
        self.parent = parent

        self.resize(160, 165)
        self.center()

        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(ICON))
        self.setFixedSize(self.size())
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # Create the automatic URL copy checkbox

        copy = self.check('Automatic URL copy', 7, 5, lambda event: self.change('copy', event))

        if self.config['copy'] == Qt.Checked:
            copy.setChecked(True)

        # Create the browser behavior checkbox

        browser = self.check('Open in the browser', 7, 30, lambda event: self.change('browser', event))

        if self.config['browser'] == Qt.Checked:
            browser.setChecked(True)

        # Create the tooltip behavior checkbox

        notification = self.check('Show notification', 7, 55, lambda event: self.change('notification', event))

        if self.config['notification'] == Qt.Checked:
            notification.setChecked(True)

        # Create the direct link activator checkbox

        short = self.check('Use direct link', 7, 80, lambda event: self.change('direct', event))

        if self.config['direct'] == Qt.Checked:
            short.setChecked(True)

        # Create the server list

        servers = self.combo(6, 105, SERVERS, lambda event: self.change('server', event))
        servers.setEditText(self.config['server'])
        servers.resize(148, 22)

        # Create unlink button

        unlink = self.button("Unlink client", 5, 130, lambda event: self.unlink(session))
        unlink.resize(150, 30)

        self.show()
        self.activateWindow()
        self.status.set(True)

    def closeEvent(self, event):

        """ Closing function of the settings
        :param event: The event which started the function
        """

        self.parent.activateWindow()
        self.status.set(False)
        self.close()

    def change(self, key, value):

        """ Set a settings parameter
        :param key: Name of the parameter
        :param value: Value of the parameter
        """

        if str(key):
            self.config[key] = value

    def unlink(self, session):

        """ Unlink client from the server, and close every window
        :param session: Status of the settings window
        """

        session.unlink()
        self.closeEvent(None)
        self.parent.closeEvent(None)


class GrabWindow(QWidget):
    disabled = Reference(False)
    settings = None
    config = None
    shape = None

    def __init__(self):

        """ Initializing the grab window """

        super(GrabWindow, self).__init__()
        self.config = Config(CONFIG)

        self.screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, self.screen.width(), self.screen.height())

        self.setWindowTitle("JamCrop")
        self.setWindowIcon(QIcon(ICON))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.shape = QRubberBand(QRubberBand.Rectangle, self)
        self.setMouseTracking(True)

        self.session = Connection(self.config)

        if not self.session.load():
            request_token = self.session.authorize()
            webbrowser.open("%s?%s" % ("https://www.dropbox.com/1/oauth/authorize",
                                       urllib.urlencode({'oauth_token': request_token['oauth_token']})))

            reply = QMessageBox.question(self, "JamCrop", "The JamCrop requires a limited Dropbox "
                                                          "access for itself. If you allowed the "
                                                          "connection to your Dropbox, from the recently "
                                                          "appeared browser window, please click on the "
                                                          "OK button. After the grab window have appeared, "
                                                          "you can open settings by pressing [F1].",
                                         QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)

            if reply == QMessageBox.Ok:
                self.session.access()
            else:
                self.closeEvent(None)
                sys.exit()

        self.activateWindow()
        self.show()

    def paintEvent(self, event):

        """ Draw an invisible layer which is clickable
        :param event: The event which started the function
        """

        canvas = QPainter()
        canvas.begin(self)
        canvas.setPen(QColor(0, 0, 0, 1))
        canvas.setBrush(QColor(0, 0, 0, 1))
        canvas.drawRect(0, 0, self.screen.width(), self.screen.height())
        canvas.end()

    def closeEvent(self, event):

        """ Closing function of the grab window
        :param event: The event which started the function
        """

        self.config.save()
        self.close()

    def keyPressEvent(self, event):

        """ Track the key presses
        :param event: The event which started the function
        """

        if event.key() == Qt.Key_F1:
            self.settings = SettingsWindow(self, self.session, self.config, self.disabled)
        elif event.key() == Qt.Key_Escape:
            self.closeEvent(None)

    def mousePressEvent(self, event):

        """ Start selecting rectangle drawing after the mouse have pressed
        :param event: Created by the pressed mouse
        """

        if not self.disabled.get():
            self.origin = event.pos()
            self.shape.setGeometry(QRect(self.origin, QSize()))
            self.shape.show()
        else:
            self.settings.activateWindow()

        QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):

        """ Draw the selecting rectangle by the mouse coordinates
        :param event: Created by the moving of the mouse
        """

        if not self.disabled.get() and self.shape.isVisible():
            self.shape.setGeometry(QRect(self.origin, event.pos()).normalized())

        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):

        """ Create the screenshot after the mouse have released
        :param event: Created by the released mouse
        """

        if not self.disabled.get() and self.shape.isVisible():
            self.shape.hide()
            self.hide()

            fileName = "%s.%s" % (str(time.strftime('%Y_%m_%d_%H_%M_%S')), self.config['img_format'])

            shot = QPixmap.grabWindow(QApplication.desktop().winId()).copy(self.shape.geometry())
            shot.save(fileName, self.config['img_format'], self.config['img_quality'])

            try:
                self.session.upload(fileName)
            except:
                self.closeEvent(None)
            finally:
                os.unlink(fileName)

            if self.config['direct'] == Qt.Checked:
                result = self.session.share(fileName, 'false')
                result['url'] += '?dl=1'
            else:
                result = self.session.share(fileName, 'true')

            if self.config['copy'] == Qt.Checked:
                pyperclip.copy(result['url'])

            if self.config['browser'] == Qt.Checked:
                webbrowser.open(result['url'])

            if self.config['notification'] == Qt.Checked:
                self.alert = Notification("JamCrop", "Uploading is completed", ICON)
                time.sleep(TIMEOUT)
                self.alert.hide()

            self.closeEvent(None)

        QWidget.mouseReleaseEvent(self, event)


def main():
    app = QApplication(sys.argv)
    crop = GrabWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
