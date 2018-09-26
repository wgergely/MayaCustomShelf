""" Custom Layout to inspect a layout from the 'camera'
#TODO: Add camera selection dropdown menu
"""

# pylint: disable=C0103

import maya.app.renderSetup.model.renderSetup as renderSetupModel  # pylint: disable=E0401
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin  # pylint: disable=E0401
import maya.cmds as cmds  # pylint: disable=E0401
import maya.OpenMayaUI as OpenMayaUI  # pylint: disable=E0401
import PySide2.QtCore as QtCore  # pylint: disable=E0401
import PySide2.QtGui as QtGui  # pylint: disable=E0401
import PySide2.QtWidgets as QtWidgets  # pylint: disable=E0401
import shiboken2  # pylint: disable=E0401
from MayaCustomShelf.mayaViewportPreset import (
    MAYA_VIEWPORT_PRESET,
    applyViewportPreset
)
from MayaCustomShelf.icons import getIconPath
from RenderSetupUtility.main.shaderUtility import ShaderUtility


class CameraLayoutWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """ A Custom Model View for Layout inspection """

    windowID = 'cameraLayout'
    wcID = '%sWorkspaceControl' % windowID

    def __init__(self, parent=None):
        MayaQWidgetDockableMixin.__init__(self)
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.ModelPanel = None

        self.setWindowTitle('Camera Layout')
        self.setObjectName(self.__class__.windowID)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Preferred
        )

        # Set window Layout
        QStackedLayout = QtWidgets.QStackedLayout()
        QStackedLayout.setObjectName(
            '%s%s' % (self.__class__.windowID, 'QStackedLayout'))
        # QStackedLayout.setContentsMargins(8,8,8,8)
        QStackedLayout.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        self.setLayout(QStackedLayout)

        self.layout().addWidget(Timecode(parent=self))
        self.QStackedLayout = QStackedLayout

        self.addModelPanel()

        self.QStackedLayout.setCurrentIndex(1)
        self.setStyleSheet(
            'QWidget {\
                padding: 0;\
                margin: 0;\
                color: rgb(150,150,150);\
            }'
        )

        cmds.evalDeferred(self.preset3Button)

    def preset1Button(self, *args):
        """Viewport Preset"""
        applyViewportPreset(self.modelPanel, MAYA_VIEWPORT_PRESET['preset1'])

    def preset2Button(self, *args):
        """Viewport Preset"""
        applyViewportPreset(self.modelPanel, MAYA_VIEWPORT_PRESET['preset2'])

    def preset3Button(self, *args):
        """Viewport Preset"""
        applyViewportPreset(self.modelPanel, MAYA_VIEWPORT_PRESET['preset3'])

    def addModelPanel(self):
        """ Adds a model panel to the window """

        # Get path
        ptr = long(shiboken2.getCppPointer(self.layout())[0])
        fullName = OpenMayaUI.MQtUtil.fullName(ptr)

        self.paneLayout = cmds.paneLayout(
            '%s%s' % (self.windowID, 'PaneLayout#'), parent=fullName)
        ptr = OpenMayaUI.MQtUtil.findControl(self.paneLayout)
        self.paneLayoutQt = shiboken2.wrapInstance(
            long(ptr), QtWidgets.QWidget)
        self.modelPanel = cmds.modelPanel(
            '%s%s' % (self.windowID, 'ModelPanel#'), parent=self.paneLayout, cam='camera')

        modelEditorIconBar = self.findChildren(
            QtWidgets.QWidget, 'modelEditorIconBar')[0]
        modelEditorIconBar.hide()

        # Adding custom style for the menu
        menubar = self.findChildren(QtWidgets.QMenuBar)[0]
        menubar.setStyleSheet(
            'QMenuBar {\
                background-color: rgba(0,0,0,0);\
                margin: 0 16 0 16;\
                padding: 0;\
                spacing: 10;\
                border: none\
            }\
            QMenuBar::item {\
                margin: 0 3;\
                padding: 0;\
                border: none;\
                border-width: 0;\
                icon-size: 20px\
            }\
            QMenuBar::item::selected {\
                background-color: rgba(255,255,255,25);\
            }'
        )

        for child in menubar.children():
            if isinstance(child, QtWidgets.QMenu):
                if child.title() in ['Help', 'Renderer', 'View']:
                    child.menuAction().setVisible(False)

        # Adding custom action buttons for pipeAka publish and burn + modelPanel view presets

        QIcon = QtGui.QIcon(getIconPath('viewAll16'))
        QAction = QtWidgets.QAction('View Preset&1', self)
        # QAction.setObjectName('viewPreset1Action')
        QAction.triggered.connect(self.preset1Button)
        QAction.setIcon(QIcon)
        menubar.addAction(QAction)

        QIcon = QtGui.QIcon(getIconPath('viewAnim16'))
        QAction = QtWidgets.QAction('View Preset&2', self)
        # QAction.setObjectName('viewPreset2Action')
        QAction.triggered.connect(self.preset2Button)
        QAction.setIcon(QIcon)
        menubar.addAction(QAction)

        QIcon = QtGui.QIcon(getIconPath('viewMesh16'))
        QAction = QtWidgets.QAction('View Preset&3', self)
        # QAction.setObjectName('viewPreset3Action')
        QAction.triggered.connect(self.preset3Button)
        QAction.setIcon(QIcon)
        menubar.addAction(QAction)


class WorkspaceControl(object):
    """Class that controls the creation and deletion of
    maya workspace controls."""

    def __init__(self, name=None):
        self.c = cmds.workspaceControl
        self.current = name
        self.exists = self._exists(name)
        self.floating = self._floating(name)

    def _exists(self, name):
        self.exists = self.c(name, q=True, exists=True)
        return self.exists

    def _floating(self, name):
        if self._exists(name):
            self.floating = self.c(name, q=True, floating=True)
            return self.floating
        return None

    def setCurrent(self, name):
        self.current = name

    def hide(self, name=None):
        if name is None:
            name = self.current
        if self._exists(name):
            self.c(name, edit=True, close=True)

    def show(self, name=None):
        if name is None:
            name = self.current
        if self._exists(name):
            self.c(name, edit=True, visible=True)

    def edit(self, name=None, **kwargs):
        if name is None:
            name = self.current
        self.c(name, edit=True, **kwargs)

    def create(self, name=None, retain=False, floating=True, delete=False):
        if name is None:
            name = self.current
        if self._exists(name):
            print '%s already exists. Skipping.' % name
            if delete:
                self.delete(name)
            return name
        else:
            name = cmds.workspaceControl(
                name, retain=retain, floating=floating)
            return name

    def delete(self, name=None):
        if name is None:
            name = self.current
            if self._exists(name):
                if self._floating(name):
                    cmds.deleteUI(name, window=True)
                else:
                    cmds.deleteUI(name, control=True)


class Timecode(QtWidgets.QWidget):
    """
    Custom bar for timecode display.
    """

    WIDTH = 680
    HEIGHT = 50

    def __init__(self, parent=None):
        super(Timecode, self).__init__(parent=parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                           QtWidgets.QSizePolicy.Fixed)
        self.setFixedHeight(self.__class__.HEIGHT)

        palette = QtGui.QPalette(self.palette())
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.transparent)
        palette.setBrush(QtGui.QPalette.Background,
                         QtGui.QBrush(QtCore.Qt.NoBrush))
        self.setPalette(palette)

        # Create layout
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addSpacing(335)  # menubar

        self.tcSpacer = QtWidgets.QSpacerItem(
            self.__class__.WIDTH, self.__class__.HEIGHT)
        layout.addItem(self.tcSpacer)

        self.setLayout(layout)
        self.layout().setAlignment(QtCore.Qt.AlignRight)

        self.setUpdatesEnabled(True)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.setInterval(30)
        timer.start()

    def getSelectionInfo(self):
        shaderUtility = ShaderUtility()
        sel = cmds.ls(selection=True)

        if len(sel) > 1:
            return 'Multiple objects selected...'
        elif not sel:
            return 'No selection'
        else:
            assignedShader = None
            for shader in shaderUtility.data:
                usedBy = shaderUtility.data[shader]['usedBy']
                if [f for f in usedBy if sel[0] in f] != []:
                    assignedShader = shader
                    break
            return '%s\n%s' % (sel[0], assignedShader)

    def paintEvent(self, event):
        TIME_PROP = int(cmds.currentTime(query=True))
        START_FRAME = int(cmds.getAttr('defaultRenderGlobals.startFrame'))
        END_FRAME = int(cmds.getAttr('defaultRenderGlobals.endFrame'))
        DURATION = END_FRAME - START_FRAME
        SCENE_NAME = str(cmds.file(query=True, sceneName=True, shortName=True))
        VISIBLE_RENDER_LAYER = renderSetupModel.instance().getVisibleRenderLayer().name()
        FRAME_RATE = cmds.currentUnit(query=True, time=True)

        FRAME_RATE = cmds.currentUnit(query=True, time=True)
        framerates = {
            'game': 15,
            'film': 24,
            'pal': 25,
            'ntsc': 30,
            'show': 48,
            'palf': 50,
            'ntscf': 60,
        }
        framerate = framerates[FRAME_RATE]

        if len(SCENE_NAME) == 0:
            SCENE_NAME = 'Scene not yet saved'

        def frames_to_timecode(frames):
            return '{0:02d}:{1:02d}:{2:02d}'.format(frames / (60 * framerate) % 60,
                                                    frames / framerate % 60,
                                                    frames % framerate)

        r = QtCore.QRect(self.tcSpacer.geometry())

        painter = QtGui.QPainter()
        font = QtGui.QFont()
        font.setStyleHint(QtGui.QFont.AnyStyle, QtGui.QFont.PreferAntialias)
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        ############################
        offset = 64

        font.setPixelSize(18)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200, 255)))
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, 0, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, str(TIME_PROP).zfill(4))
        ############################
        offset += 108

        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200, 255)))
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, 0, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                         str(frames_to_timecode(TIME_PROP)) + '   |')

        ############################
        offset += 35

        font.setPixelSize(12)
        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200, 255)))
        font.setBold(True)
        painter.setFont(font)

        string = '%s' % (framerate)
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, -6, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)

        string = '%s' % (DURATION)
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, 6, r.width(), r.height())
        painter.drawText(rect,  QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)

        ############################
        offset += 65

        painter.setPen(QtGui.QPen(QtGui.QColor(150, 150, 150, 255)))
        font.setBold(False)
        painter.setFont(font)

        string = '%s:' % ('Framerate')
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, -7, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)

        string = '%s:' % ('Duration')
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, 7, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)

        ############################
        offset += 40

        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200, 255)))
        font.setBold(True)
        painter.setFont(font)

        string = '%s' % (START_FRAME)
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, -7, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)

        string = '%s' % (END_FRAME)
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, 7, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)
        # ############################
        offset += 70

        painter.setPen(QtGui.QPen(QtGui.QColor(150, 150, 150, 255)))
        font.setBold(False)
        painter.setFont(font)

        string = '%s:' % ('Start Frame')
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, -7, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)

        string = '%s:' % ('End Frame')
        rect = QtCore.QRect(r.x() + self.__class__.WIDTH -
                            offset, 7, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignLeft |
                         QtCore.Qt.AlignVCenter, string)

        ############################
        offset += 32

        font.setBold(True)
        painter.setPen(QtGui.QPen(QtGui.QColor(110, 110, 255, 255)))
        painter.setFont(font)
        string = '%s\n%s' % (VISIBLE_RENDER_LAYER, SCENE_NAME)
        rect = QtCore.QRect(r.x() - offset, 0, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignRight |
                         QtCore.Qt.AlignVCenter, string)

        ############################
        offset += len(SCENE_NAME) * 8

        font.setBold(True)
        painter.setPen(QtGui.QPen(QtGui.QColor(110, 110, 255, 255)))
        painter.setFont(font)
        string = '%s' % (self.getSelectionInfo())
        rect = QtCore.QRect(r.x() - offset, 0, r.width(), r.height())
        painter.drawText(rect, QtCore.Qt.AlignRight |
                         QtCore.Qt.AlignVCenter, string)

        painter.end()
