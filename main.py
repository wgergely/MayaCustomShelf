""" Custom toolbar for Maya.
The toolbar embeds itself into the viewport and adds buttons to the main window
and to toggle between viewport presets.
"""

# pylint: disable=C0103

import base64
import os
import tempfile

import maya.cmds as cmds  # pylint: disable=E0401
import maya.OpenMayaUI as OpenMayaUI  # pylint: disable=E0401
import PySide2.QtWidgets as QtWidgets  # pylint: disable=E0401
import RenderSetupUtility
import shiboken2  # pylint: disable=E0401

from MayaCustomShelf.customCamera import CAMERA_TEMPLATE
from MayaCustomShelf.mayaViewportPreset import (MAYA_VIEWPORT_PRESET,
                                                applyViewportPreset)
from MayaCustomShelf.Tools.customCameraLayoutView import CameraLayoutWindow
from MayaCustomShelf.Tools.randomizedDuplicate import RandomDuplicate
from MayaCustomShelf.utils import QGet, getIconPath

SCRIPT_NAME = 'MayaCustomShelf'
windowID = '{}Window'.format(SCRIPT_NAME)
windowTitle = 'Gergely\'s Custom Toolset'
windowPrefix = 'MCShelf'
tempDir = tempfile.gettempdir()


windowSize = (600, 32)
margin = (8, 0)
color = 0.23


MENU_MODES = (
    'Modeling',
    'Rendering',
    'Animation',
    'Rigging'
)


def separator(*args):  # pylint: disable=W0613
    """ Separator """
    pass


def rsUtility(*args):  # pylint: disable=W0613
    """Show RenderSetupUtility Window"""
    RenderSetupUtility.show()


def importCameraPresetScene(*args):  # pylint: disable=W0613
    """ Imports the camera into the scene """

    tempMaya = 'cameraTemplate.mb'
    p = os.path.join(tempDir, tempMaya)
    p = os.path.normpath(p)
    f = open(p, mode='w')
    f.write(base64.b64decode(CAMERA_TEMPLATE))
    f.close()

    if cmds.objExists('camera'):
        raise RuntimeWarning('An object named camera already exists.')

    cmds.file(p, i=True, defaultNamespace=True)


def viewPreset1(*args):  # pylint: disable=W0613
    modelPanelName = cmds.getPanel(withFocus=True)
    applyViewportPreset(modelPanelName, MAYA_VIEWPORT_PRESET['preset1'])


def viewPreset2(*args):  # pylint: disable=W0613
    modelPanelName = cmds.getPanel(withFocus=True)
    applyViewportPreset(modelPanelName, MAYA_VIEWPORT_PRESET['preset2'])


def viewPreset3(*args):  # pylint: disable=W0613
    modelPanelName = cmds.getPanel(withFocus=True)
    applyViewportPreset(modelPanelName, MAYA_VIEWPORT_PRESET['preset3'])


def toggleFullScreen(*args):
    """Toggle full screen mode"""

    TEMPLATE = {
        'Shelf': True,
        'Outliner': False,
        'NEXDockControl': False,
        'MainPane': False,
        'ToolBox': True,
        'TimeSlider': False,
        'RangeSlider': True,
        'CommandLine': True,
        'StatusLine': True,
        'HelpLine': True,
    }

    def getQt(string):
        """private function - returns a qobject"""
        ptr = OpenMayaUI.MQtUtil.findControl(string)
        qtItem = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
        parent = qtItem.parent()
        if parent:
            gparent = parent.parent()
            if gparent:
                return gparent
            else:
                return parent

    o = QGet()

    mode = True
    for k in TEMPLATE:
        item = getQt(k)
        if TEMPLATE[k] and item:
            if item.isHidden() is True:
                mode = True
                break
            else:
                mode = False
                break

    # Maya MainWindow children visibility
    if mode is True:
        # menuBar.show()
        o.mayaMainWindow.showMaximized()
        for k in TEMPLATE:
            item = getQt(k)
            if TEMPLATE[k] and item:
                item.show()
    if mode is False:
        # menuBar.hide()
        o.mayaMainWindow.showFullScreen()
        for k in TEMPLATE:
            item = getQt(k)
            if TEMPLATE[k] and item:
                item.hide()

    # model editor icon bars
    for modelPanel in cmds.getPanel(type='modelPanel'):
        if modelPanel in ['modelPanel1', 'modelPanel2', 'modelPanel3', 'modelPanel4']:
            ptr = OpenMayaUI.MQtUtil.findControl(modelPanel)
            if not ptr:
                continue
            modelPanelQt = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
            iconbar = modelPanelQt.findChildren(
                QtWidgets.QWidget, 'modelEditorIconBar')[0]

            if mode is True:
                iconbar.show()
            if mode is False:
                iconbar.hide()

    # outliner
    outliner = getQt('Outliner')
    if outliner is not None:
        outlinerTabBar = outliner.findChildren(QtWidgets.QTabBar)[0]

        if mode is True:
            outlinerTabBar.show()
            for obj in outliner.findChildren(QtWidgets.QScrollBar):
                obj.show()
        if mode is False:
            outlinerTabBar.hide()
            for obj in outliner.findChildren(QtWidgets.QScrollBar):
                o.setWidget(obj)
                obj.hide()

# Modeling tools


def mirrorMesh(axis):
    """
    Mirror mesh based on world axis.
    """

    # Axis to mirror
    SET_AXIS = axis
    MERGE_MODE = 1  # 0: don't merge 1: merge edges
    MERGE_THRESHOLD = 0.1

    modes = {
        'x': 0,
        'y': 1,
        'z': 2,
        '-x': 0,
        '-y': 1,
        '-z': 2,
    }

    axis = modes[[f for f in modes if f == SET_AXIS][0]]
    negative = '-' in SET_AXIS

    sel = cmds.ls(selection=True)
    hilite = cmds.ls(hilite=True)
    sel = list(set(sel + hilite))

    cmds.hilite(replace=True)
    cmds.select(sel)
    # Reset mesh
    for s in sel:
        cmds.cutKey(s, shape=True, hierarchy='both')
        cmds.makeIdentity(apply=True)
        cmds.delete(s, constructionHistory=True)

    rel = cmds.listRelatives(sel, shapes=True)
    selectionSet = []

    def boundingBox(name):
        """ get bounding box """

        def average(l):
            """private function"""
            return (l[0] + l[1]) / len(list)
        arr = []
        for lst in cmds.polyEvaluate(
                name,
                boundingBoxComponent=True,
                accurateEvaluation=True
        ):
            arr.append(average(lst))
        return arr

    if rel is None:
        raise RuntimeError('Select a mesh object to continue.')
    if cmds.objectType(rel[0], isType='mesh') is False:
        raise RuntimeError('Select a mesh object to continue.')

    for r in rel:
        numFaces = cmds.polyEvaluate(r, face=True)
        for f in xrange(numFaces):
            name = '%s.f[%s]' % (r, f)
            cmds.select(name, replace=True)
            xyz = boundingBox(name)

            if (xyz[axis] <= 0) is negative:
                selectionSet.append(name)

    cmds.select(clear=True)
    cmds.hilite(sel)
    cmds.select(selectionSet, replace=True)
    cmds.delete()

    for s in sel:
        cmds.polyMirrorFace(s, worldSpace=True, pivot=(0, 0, 0), mergeMode=MERGE_MODE,
                            mergeThreshold=MERGE_THRESHOLD, direction=axis, constructionHistory=True)

    if hilite:
        cmds.hilite(hilite, replace=True)

    else:
        cmds.select(sel)


def resetMesh():
    sel = cmds.ls(selection=True, long=True)
    for s in sel:
        cmds.cutKey(s, shape=True, hierarchy='both')
        cmds.makeIdentity(apply=True)
        cmds.delete(s, constructionHistory=True)


def layoutWindow(*args):
    """ Opens a new Custom Layout window """

    window = CameraLayoutWindow()
    window.show(dockable=True, retain=False)

    o = QGet()
    win = o.getByWindowTitle('Camera Layout')
    if QtWidgets.QDesktopWidget().screenCount() == 1:
        win.showNormal()
    if QtWidgets.QDesktopWidget().screenCount() >= 2:
        win.showMaximized()

    applyViewportPreset(window.modelPanel, MAYA_VIEWPORT_PRESET['preset1'])


def randomizedDuplicate(*args):
    """Show the Random Duplicate UI"""
    RandomDuplicate().createUI()


def setMenuMode(arg):
    """Switch menu working mode"""
    s = '%sMenuSet' % (arg.lower())
    cmds.setMenuMode(s)


def createUI():
    tabIdx = -1
    btnIdx = -1
    shelfIdx = -1
    btnCmds = []

    mayaMainWindowPointer = OpenMayaUI.MQtUtil.mainWindow()
    mayaMainWindow = shiboken2.wrapInstance(
        long(mayaMainWindowPointer), QtWidgets.QWidget)

    try:
        cmds.deleteUI('%s' % (windowID))
        cmds.deleteUI('%s%s' % (windowID, 'WorkspaceControl'))
    except Exception:
        pass

    window = QtWidgets.QWidget()
    window.setWindowTitle('Custom Toolset')
    window.parent = mayaMainWindow
    window.setObjectName(windowID)
    window.setContentsMargins(0, 0, 0, 0)
    window.setFixedHeight(32 + 4)
    # window.setSpacing(0)

    workspacePanel1 = mayaMainWindow.children()[6]
    mayaLayoutInternalWidget = workspacePanel1.children()[2]
    mainWorkBar = mayaLayoutInternalWidget.children()[4]
    viewports = mainWorkBar.children()[1]

    window.show()
    shelfIdx += 1
    cmds.shelfLayout(
        '%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        parent=windowID,
        style='iconOnly',
        width=windowSize[0],
        height=32,
        cellWidthHeight=[windowSize[1] + margin[0]] * 2,
        # backgroundColor=[color+0.05]*3,
        preventOverride=True
    )

    # Separator
    btnIdx += 1
    btnCmds.append(separator)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=btnCmds[btnIdx],
        enable=False
    )
    btnIdx += 1
    btnCmds.append(rsUtility)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('rsUtility32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    # Separator
    btnIdx += 1
    btnCmds.append(separator)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=btnCmds[btnIdx],
        enable=False
    )
    btnIdx += 1
    btnCmds.append(importCameraPresetScene)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('newCamera32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    btnIdx += 1
    btnCmds.append(viewPreset1)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('viewAll32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    btnIdx += 1
    btnCmds.append(viewPreset2)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('viewAnim32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    btnIdx += 1
    btnCmds.append(viewPreset3)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('viewMesh32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    btnIdx += 1
    btnCmds.append(toggleFullScreen)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('toggleFullScreen32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    # Separator
    btnIdx += 1
    btnCmds.append(separator)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=btnCmds[btnIdx],
        enable=False
    )

    cmds.optionMenu(
        '%s_menuModes' % ('gwCustomShelf'),
        width=85,
        height=windowSize[1],
        annotation='',
        backgroundColor=[color + 0.05] * 3,
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        changeCommand=setMenuMode
    )
    for item in MENU_MODES:
        cmds.menuItem(item, enableCommandRepeat=True, command=setMenuMode)

    # Separator
    btnIdx += 1
    btnCmds.append(separator)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=btnCmds[btnIdx],
        enable=False
    )

    btnIdx += 1
    btnCmds.append(layoutWindow)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('viewPreset132'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    # Separator
    btnIdx += 1
    btnCmds.append(separator)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=btnCmds[btnIdx],
        enable=False
    )
    btnIdx += 1
    btnCmds.append(randomizedDuplicate)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('randomizedDuplicate32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    # Separator
    btnIdx += 1
    btnCmds.append(separator)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=btnCmds[btnIdx],
        enable=False
    )
    btnIdx += 1

    def mirrorMeshX2():
        mirrorMesh('-x')
    btnCmds.append(mirrorMeshX2)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('mirrorModeX232'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    btnIdx += 1

    def mirrorMeshX1():
        mirrorMesh('x')
    btnCmds.append(mirrorMeshX1)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('mirrorModeX132'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )
    btnIdx += 1
    btnCmds.append(resetMesh)
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=windowSize[1],
        height=windowSize[1],
        marginWidth=0,
        marginHeight=0,
        align='center',
        image=getIconPath('resetMesh32'),
        useAlpha=True,
        flat=True,
        version='2017',
        sourceType='python',
        command=btnCmds[btnIdx]
    )

    # ptr = OpenMayaUI.MQtUtil.findControl('Outliner')
    # OutlinerQt = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
    ptr = OpenMayaUI.MQtUtil.findControl('NEXDockControl')
    NEXDockControlQt = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
    ptr = OpenMayaUI.MQtUtil.findControl('MainPane')
    MainPaneQt = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
    ptr = OpenMayaUI.MQtUtil.findControl('ToolBox')
    ToolBoxQt = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)

    layout = MainPaneQt.layout()
    layout.insertWidget(0, window)
