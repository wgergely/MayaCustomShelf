""" Utility functions """

# pylint: disable=C0103

import os
import base64
import tempfile
import shiboken2 # pylint: disable=E0401

import maya.OpenMayaUI as OpenMayaUI # pylint: disable=E0401

try:
    import mtoa.ui.arnoldmenu as arnoldmenu # pylint: disable=E0401
except RuntimeError:
    print '# Error importing mtoa'

import PySide2.QtCore as QtCore # pylint: disable=E0401
import PySide2.QtWidgets as QtWidgets # pylint: disable=E0401

from MayaCustomShelf.icons import icons

SCRIPT_NAME = 'MayaCustomShelf'
windowID = '{}Window'.format(SCRIPT_NAME)
windowTitle = 'Gergely\'s Custom Toolset'
windowPrefix = 'MCShelf'
tempDir = tempfile.gettempdir()


def getIconPath(string):
    """ Returns the path for a given icon name """


    p = os.path.normpath(
        os.path.join(
            tempDir,
            '%s_%s.%s' % (windowPrefix, string, 'png')
        )
    )

    if os.path.exists(p):
        return p
    return None


def writeIconsToTempDir(string):
    """ Save binary data to file """

    p = os.path.normpath(os.path.join(tempDir, '%s_%s.%s' %
                                      (windowPrefix, string, 'png')))
    f = open(p, 'w')
    f.write(base64.b64decode(icons[string]))

for k in icons:
    writeIconsToTempDir(k)

class QGet(QtCore.QObject):
    """ Gets and stores a QT item """

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self)
        # super(QGet, self).__init__(parent=parent)

        ptr = OpenMayaUI.MQtUtil.mainWindow()
        mayaMainWindow = shiboken2.wrapInstance(
            long(ptr), QtWidgets.QMainWindow)
        self.allWidgets = QtWidgets.QApplication.allWidgets
        self.mayaMainWindow = mayaMainWindow
        self.QRenderView = None
        self.QRenderViewControl = None
        self.widget = None

    def getQRenderView(self, printInfo=False, query=False):
        """Return the renderview"""

        def _set():
            """Private method"""
            for obj in self.allWidgets():
                if type(obj) is QtWidgets.QMainWindow:
                    if obj.windowTitle() == 'Arnold Render View':
                        self.QRenderView = obj
                        break
            for obj in self.allWidgets():
                if type(obj) is QtWidgets.QWidget:
                    if obj.windowTitle() == 'Arnold RenderView':
                        self.QRenderViewControl = obj
                        break
        _set()
        if self.QRenderView is None and query is False:
            arnoldmenu.arnoldMtoARenderView()
            _set()

        if printInfo:
            self._printInfo(self.QRenderView)
        return self.QRenderView

    def getByWindowTitle(self, string):
        """Private method"""
        for obj in self.allWidgets():
            if type(obj) is QtWidgets.QWidget:
                if obj.windowTitle() == string:
                    self.widget = obj
        return self.widget

    def getByObjectName(self, string):
        """Private method"""
        for obj in self.allWidgets():
            if type(obj) is QtWidgets.QWidget:
                if obj.objectName() == string:
                    self.widget = obj
        return self.widget

    def setWidget(self, QItem):
        """Private method"""
        self.widget = QItem


class EventFilter(QtCore.QObject):
    """
    Event filter which emits a parent_closed signal whenever
    the monitored widget closes.

    via:
    https: // github.com / shotgunsoftware / tk - maya /
    blob / master / python / tk_maya / panel_util.py
    """

    def __init__(self):
        self._widget_id = None

    def set_associated_widget(self, widget_id):
        """
        Set the widget to effect
        """
        self._widget_id = widget_id

    @staticmethod
    def eventFilter(obj, event):
        """
        QT Event filter callback

        : param obj: The object where the event originated from
        : param event: The actual event object
        : returns: True if event was consumed, False if not
        """

        if event.type() == QtCore.QEvent.Type.Close:
            print 'CloseEvent'

        return False
