#!/usr/bin/env python
#-*- coding: utf-8 -*-
from PyQt4 import Qt

__author__ = "Tornyi Dénes"
__version__ = "1.0.0"


SERVER = 'jamcropxy.appspot.com'
CONFIG = 'config.xml'
ICON = 'icon.ico'


from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from xml.etree.ElementTree import ElementTree
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import webbrowser
import urlparse
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


class Window(QWidget):
    def center(self):
        frame = self.frameGeometry()
        screen = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    def label(self, msg, x, y):
        label = QLabel(msg, self)
        label.move(x, y)
        return label

    def button(self, title, x, y, onclick = False):
        button = QPushButton(title, self)
        button.resize(button.sizeHint())
        button.move(x, y)

        if onclick:
            button.clicked.connect(onclick);

        return button

    def field(self, x, y, w, h, value = False, action = False):
        field = QLineEdit(self)
        field.setMaxLength(64)
        field.move(x, y)
        field.resize(w, h)

        if value:
            field.setText(value)
        if action:
            field.textEdited.connect(action)

        return field

    def check(self, desc, x, y, action = False):
        check = QCheckBox(desc, self)
        check.move(x, y)

        if action:
            check.stateChanged.connect(action);

        return check


class Notification(QSystemTrayIcon):
    def __init__(self, title, msg, icon, timeout = 2500, parent = None):
        QSystemTrayIcon.__init__(self, parent)
        self.setIcon(QIcon(icon))
        self.show()
        self.showMessage(title, msg, msecs = timeout)


class SettingsWindow(Window):
    session = None
    config = None
    status = None

    def __init__(self, parent, session, config, status = Reference(False)):
        Window.__init__(self)
        self.config = config
        self.status = status
        self.parent = parent

        self.resize(130, 140)
        self.center()

        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(ICON))
        self.setFixedSize(self.size())
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # Create the automatic URL copy checkbox

        copy = self.check('Automatic URL copy', 7, 5, lambda event: self.set('copy', event))

        if self.config['copy'] == 'true':
            copy.setChecked(True)

        # Create the browser behavior checkbox

        browser = self.check('Open in the browser', 7, 30, lambda event: self.set('browser', event))

        if self.config['browser'] == 'true':
            browser.setChecked(True)

        # Create the tooltip behavior checkbox

        notification = self.check('Show notification', 7, 55, lambda event: self.set('notification', event))

        if self.config['notification'] == 'true':
            notification.setChecked(True)

        # Create the direct link activator checkbox

        short = self.check('Use direct link', 7, 80, action = lambda event: self.set('short', event))

        if self.config['short'] == 'true':
            short.setChecked(True)

        # Create the button to unlink the client

        unlink = self.button("Unlink client", 5, 105, lambda event: self.unlink(session))
        unlink.resize(120, 30)

        self.show()
        self.activateWindow()
        self.status.set(True)

    def closeEvent(self, event):
        self.parent.activateWindow()
        self.status.set(False)
        self.close()

    def set(self, key, value):
        if value == Qt.Checked:
            self.config[key] = 'true'
        elif value == Qt.Unchecked:
            self.config[key] = 'false'

    def unlink(self, session):
        session.unlink()
        self.closeEvent(None)
        self.parent.closeEvent(None)

class GrabWindow(QWidget):
    disabled = Reference(False)
    settings = None
    config = None
    shape = None

    def __init__(self):
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

        if(not self.session.load()):
            request_token = self.session.authorize()
            webbrowser.open("%s?%s" % ("https://www.dropbox.com/1/oauth/authorize",
                                       urllib.urlencode({'oauth_token' : request_token['oauth_token']})))

            reply = QMessageBox.question(self, "JamCrop", "The JamCrop require a limited Dropbox"
                                                                " access for itself. If you allowed the "
                                                                "connection to the Dropbox, from the recently "
                                                                "appeared browser window, please click on the "
                                                                "OK button. After the grab window have appeared, "
                                                                "you can open settings by pressing [F1].",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.session.access()
            else: return

        self.activateWindow()
        self.show()

    def paintEvent(self, event):
        canvas = QPainter()
        canvas.begin(self)
        canvas.setPen(QColor(0, 0, 0, 1))
        canvas.setBrush(QColor(0, 0, 0, 1))
        canvas.drawRect(0, 0, self.screen.width(), self.screen.height())
        canvas.end()

    def closeEvent(self, event):
        self.config.save()
        self.close()
        sys.exit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            self.settings = SettingsWindow(self, self.session, self.config, self.disabled)
        elif event.key() == Qt.Key_Escape:
            self.closeEvent(None)

    def mousePressEvent(self, event):
        if not self.disabled.get():
            self.origin = event.pos()
            self.shape.setGeometry(QRect(self.origin, QSize()))
            self.shape.show()
        else:
            self.settings.activateWindow()
        QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if not self.disabled.get() and self.shape.isVisible():
            self.shape.setGeometry(QRect(self.origin, event.pos()).normalized())
        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if not self.disabled.get() and self.shape.isVisible():
            self.shape.hide()
            self.hide()

            fileName = "%s.jpg" % str(time.strftime('%Y_%m_%d_%H_%M_%S'))

            shot = QPixmap.grabWindow(QApplication.desktop().winId()).copy(self.shape.geometry())
            shot.save(fileName, 'jpg')

            self.session.upload(fileName)
            os.unlink(fileName)

            result = self.session.share(fileName, self.config['short'])

            if self.config['short'] == 'false':
                result['url'] += '?dl=1'

            if self.config['copy'] == 'true':
                QApplication.clipboard().setText(QString(result['url']), QClipboard.Clipboard)

            if self.config['browser'] == 'true':
                webbrowser.open(result['url'])

            if self.config['notification'] == 'true':
                self.alert = Notification("JamCrop", "Uploading is completed", ICON)

            self.closeEvent(None)

        QWidget.mouseReleaseEvent(self, event)


def main():
    app = QApplication(sys.argv)
    crop = GrabWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()