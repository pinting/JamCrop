#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-


__author__ = ['Dénes Tornyi', 'Ádam Tajti']
__version__ = "2.0.4"


# Network protocol (http or https)
PROTOCOL = 'http'
# Notification timeout
TIMEOUT = 2.5
# Content of the server list in settings
SERVERS = ['jamcropxy.appspot.com']
# Possible formats
FORMATS = ['jpg', 'png']
# Config file
CONFIG = 'config.json'
# Maximum amount of retry
RETRY = 5
# Icon of the application
ICON = 'icon.ico'


from poster.streaminghttp import register_openers
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import webbrowser
import functools
import pyperclip
import mimetypes
import cStringIO
import urlparse
import urllib2
import urllib
import json
import time
import sys


class Reference:

    """ Reference class is used to store a single variable, that is referable. """

    def __init__(self, var):
        self.var = var

    def get(self):

        """ Gets the value of the variable. """

        return self.var

    def set(self, var):

        """ Sets the value of the variable. """

        self.var = var


class Connection:
    request_token = None
    access_token = None
    config = None

    def __init__(self, config):
        self.config = config

    class retry(object):

        """ Retry decorator for the Connection class functions. """

        method = None
        attempt = RETRY

        def __init__(self, method):
            self.method = method

        def __get__(self, *obj):
            return functools.partial(self.__call__, obj[0])

        def __call__(self, *args, **kwargs):
            try:
                return self.method(*args, **kwargs)
            except:
                if(self.attempt):
                    time.sleep(1)
                    self.attempt -= 1
                    return self.__call__(*args, **kwargs)
                raise

    @retry
    def authorize(self):

        """ Gets a request token. """

        result = urllib2.urlopen('%s://%s/authorize' % (PROTOCOL, self.config['server']))
        self.request_token = dict(urlparse.parse_qsl(result.read()))
        return self.request_token

    @retry
    def access(self):

        """ Gets an access token, using the request token. """

        result = urllib2.urlopen('%s?%s' % ('%s://%s/access' % (PROTOCOL, self.config['server']),
                                            urllib.urlencode(self.request_token)))
        self.access_token = dict(urlparse.parse_qsl(result.read()))
        self.config['token'] = urllib.urlencode(self.access_token)
        return self.access_token

    @retry
    def upload(self, stringIO, fileName):

        """ Uploads a file to the server. """

        headers = {'content-type': mimetypes.guess_type(fileName)[0],
                   'content-length': str(len(stringIO.read()))}

        opener = register_openers()
        request = urllib2.Request('%s?%s' % ('%s://%s/upload' % (PROTOCOL, self.config['server']),
                                             urllib.urlencode(dict(self.access_token.items() +
                                                         dict({'name': fileName}).items()))), stringIO, headers)
        return json.loads((opener.open(request).read()))

    @retry
    def geturl(self, fileName, shortURL = 'false'):

        """ Gets back the link of the uploaded file. """

        request = urllib2.Request('%s?%s' % ('%s://%s/share' % (PROTOCOL, self.config['server']),
                                             urllib.urlencode(dict(self.access_token.items() +
                                                                dict({'name': fileName, 'short': shortURL}).items()))))
        return json.loads((urllib2.urlopen(request)).read())

    def load(self):

        """ Loads the token if we have it, else it returns false. """

        if self.config['token'] is not None:
            self.access_token = dict(urlparse.parse_qsl(self.config['token']))
            return True
        else:
            return False

    def unlink(self):

        """ Deletes the token from the config. """

        self.config['token'] = None


class Config:

    """ Config class used to read and write JSON data. """

    config = None
    fileName = None

    def __init__(self, fileName):
        self.fileName = fileName
        with open(self.fileName, 'r') as config_file:
            self.config = json.load(config_file)

    def __setitem__(self, key, value):
        self.config[key] = unicode(value)

    def __getitem__(self, key):
        try:
            if isinstance(self.config[key], int):
                # If it is Integer
                return int(self.config[key])
            else:
                # If it is Float/Double
                return float(self.config[key])
        except (ValueError, TypeError):
            if self.config[key] == 'None':
                # If it is None
                return None
            # If it is String
            return self.config[key]
        except:
            raise Exception('Not found!')

    def save(self):
        try:
            with open(self.fileName, 'w') as config_file:
                json.dump(self.config, config_file, indent = 4)
        except IOError as error:
            raise IOError('Cannot write the config (%s)!' % error)


class Window(QWidget):
    def center(self):

        """ Moves the window to the center of the screen. """

        frame = self.frameGeometry()
        screen = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    def label(self, msg, x, y):

        """ Creates a new label. """

        label = QLabel(msg, self)
        label.move(x, y)
        return label

    def button(self, msg, x, y, action = False):

        """ Creates a new button.
        :param action: An action to take when the button is clicked.
        """

        button = QPushButton(msg, self)
        button.resize(button.sizeHint())
        button.move(x, y)

        if action:
            button.clicked.connect(action)

        return button

    def field(self, x, y, w, h, default = False, action = False):

        """ Creates a new field.
        :param default: Default text.
        :param action: An action to take when the text changes.
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

    def check(self, msg, x, y, action = False):

        """ Creates a new checkbox.
        :param action: An action to take when the state of the checkbox changes.
        """

        check = QCheckBox(msg, self)
        check.move(x, y)

        if action:
            check.stateChanged.connect(action)

        return check

    def combo(self, x, y, values, action = False):

        """ Creates a new combobox.
        :param action: An action to take when the text of the combobox changes.
        """

        combo = QComboBox(self)
        combo.setEditable(True)
        combo.addItems(values)
        combo.move(x, y)

        if action:
            combo.editTextChanged.connect(action)

        return combo


class Notification(QSystemTrayIcon):
    def __init__(self, title, msg, icon = ICON, parent = None):
        QSystemTrayIcon.__init__(self, parent)
        self.setIcon(QIcon(icon))
        self.show()
        self.showMessage(title, msg)

class SettingsWindow(Window):
    session = None
    config = None
    status = None

    def __init__(self, parent, session, config, status = Reference(False)):
        Window.__init__(self)
        self.config = config
        self.status = status
        self.parent = parent

        self.resize(160, 190)
        self.center()

        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(ICON))
        self.setFixedSize(self.size())
        self.setWindowFlags(Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # Automatic URL copy activator checkbox

        copyBox = self.check('Automatic URL copy', 7, 5, lambda event: self.change('copy', event))

        if self.config['copy'] == Qt.Checked:
            copyBox.setChecked(True)

        # Browser activator checkbox

        browserBox = self.check('Open in the browser', 7, 30, lambda event: self.change('browser', event))

        if self.config['browser'] == Qt.Checked:
            browserBox.setChecked(True)

        # Notification activator checkbox

        notifyBox = self.check('Show notification', 7, 55, lambda event: self.change('notification', event))

        if self.config['notification'] == Qt.Checked:
            notifyBox.setChecked(True)

        # Direct link activator checkbox

        shortBox = self.check('Use direct link', 7, 80, lambda event: self.change('direct', event))

        if self.config['direct'] == Qt.Checked:
            shortBox.setChecked(True)

        # Format list

        formatList = self.combo(6, 105, FORMATS, lambda event: self.change('format', event))
        formatList.setEditText(self.config['format'])
        formatList.resize(148, 22)

        # Server list

        serverList = self.combo(6, 130, SERVERS, lambda event: self.change('server', event))
        serverList.setEditText(self.config['server'])
        serverList.resize(148, 22)

        # Unlink button

        unlinkBtn = self.button("Unlink client", 5, 155, lambda event: self.unlink(session))
        unlinkBtn.resize(150, 30)

        self.show()
        self.activateWindow()
        self.status.set(True)

    def closeEvent(self, event):

        """ Closes the settings window. """

        self.parent.activateWindow()
        self.status.set(False)
        self.close()

    def change(self, key, value):

        """ Sets a config attribute identified by the key. """
        
        self.config[key] = value

    def unlink(self, session):

        """ Disconnects from the server, and closes every window.
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
            request_token = error((urllib2.URLError), self.session.authorize)
            if(request_token is True):
                self.alert = Notification("JamCrop", "The server in unavailable!")
                time.sleep(TIMEOUT)
                self.alert.hide()
                sys.exit(-1)
            webbrowser.open("%s%s?%s" % (PROTOCOL, "://www.dropbox.com/1/oauth/authorize",
                                         urllib.urlencode({'oauth_token': request_token['oauth_token']})))

            reply = QMessageBox.question(self, "JamCrop", "The JamCrop requires a limited Dropbox "
                                                          "access for itself. If you allowed the "
                                                          "connection to your Dropbox, from the recently "
                                                          "appeared browser window, please click on the "
                                                          "OK button. After the grab window have appeared, "
                                                          "you can open settings by pressing [F1].",
                                         QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply != QMessageBox.Ok or error((urllib2.URLError), self.session.access) is True:
                if reply == QMessageBox.Ok:
                    self.alert = Notification("JamCrop", "The server in unavailable!")
                    time.sleep(TIMEOUT)
                    self.alert.hide()
                sys.exit(-1)

        self.activateWindow()
        self.show()

    def paintEvent(self, event):

        """ Draws an invisible layer, which is clickable. """

        canvas = QPainter()
        canvas.begin(self)
        canvas.setPen(QColor(0, 0, 0, 1))
        canvas.setBrush(QColor(0, 0, 0, 1))
        canvas.drawRect(0, 0, self.screen.width(), self.screen.height())
        canvas.end()

    def closeEvent(self, event):

        """ Saves the config, and closes the window. """

        self.config.save()
        self.close()

    def keyPressEvent(self, event):

        """ Keypress event handler. """

        if event.key() == Qt.Key_F1:
            self.settings = SettingsWindow(self, self.session, self.config, self.disabled)
        elif event.key() == Qt.Key_Escape:
            self.closeEvent(None)

    def mousePressEvent(self, event):

        """ Draws a rectangle for selecting purposes after the mouse has been pressed. """

        if not self.disabled.get():
            self.origin = event.pos()
            self.shape.setGeometry(QRect(self.origin, QSize()))
            self.shape.show()
        else:
            self.settings.activateWindow()

        QWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):

        """ Draws the selecting rectangle by the mouse coordinates. """

        if not self.disabled.get() and self.shape.isVisible():
            self.shape.setGeometry(QRect(self.origin, event.pos()).normalized())

        QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):

        """ Captures and uploads the screenshot after the mouse has been released. """

        if not self.disabled.get() and self.shape.isVisible():
            self.shape.hide()
            self.hide()

            fileName = "%s.%s" % (str(time.strftime('%Y_%m_%d_%H_%M_%S')), self.config['format'])

            # Moves the QPixmap into a cStringIO object
            pixmap = QPixmap.grabWindow(QApplication.desktop().winId()).copy(self.shape.geometry())
            byteArray = QByteArray()
            buffer = QBuffer(byteArray)
            buffer.open(QIODevice.WriteOnly)
            pixmap.save(buffer, self.config['format'], self.config['quality'])

            stringIO = cStringIO.StringIO(byteArray)
            stringIO.seek(0)

            # Uploads the screenshot
            if error((urllib2.URLError), self.session.upload, stringIO, fileName) is True:
                self.alert = Notification("JamCrop", "An error occurred in the uploading!")
                time.sleep(TIMEOUT)
                self.alert.hide()
                self.closeEvent(None)
                sys.exit(-1)

            # Gets the URL of the screenshot if it is needed
            if self.config['copy'] or self.config['browser']:
                try:
                    if self.config['direct'] == Qt.Checked:
                        result = self.session.geturl(fileName, 'false')
                        result['url'] += '?dl=1'
                    else:
                        result = self.session.geturl(fileName, 'true')
                except urllib2.URLError:
                    self.alert = Notification("JamCrop", "An error occurred while trying to get the URL!")
                    time.sleep(TIMEOUT)
                    self.alert.hide()
                    self.closeEvent(None)
                    sys.exit(-1)

            # Copies the URL to the clipboard
            if self.config['copy']:
                pyperclip.copy(result['url'])

            # Opens the URL in the browser
            if self.config['browser']:
                webbrowser.open(result['url'])

            # Notifies the user about the successful upload
            if self.config['notification']:
                msg = "Your screenshot is uploaded!"
                if self.config['copy']:
                    msg += "\nIt is on your clipboard!"
                self.alert = Notification("JamCrop", msg)
                time.sleep(TIMEOUT)
                self.alert.hide()

            self.closeEvent(None)

        QWidget.mouseReleaseEvent(self, event)


def error(name, function, *args, **kwargs):

    """ Error handling helping function
    :param name: Tuple list of the excepting errors
    :param function: Name of the functions
    :param args: Normals arguments of the named functions
    :param kwargs: Keyword arguments
    """

    try:
        return function(*args, **kwargs)
    except name:
        return True


def main():
    app = QApplication(sys.argv)
    crop = GrabWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
