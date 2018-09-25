""" Custom toolbar for Maya.
The toolbar embeds itself into the viewport and adds buttons to the main window
and to toggle between viewport presets.
"""

# pylint: disable=C0103

import base64
import os
import tempfile
import imp
import sys

import PySide2.QtWidgets as QtWidgets  # pylint: disable=E0401
import shiboken2  # pylint: disable=E0401

import maya.cmds as cmds  # pylint: disable=E0401
import maya.OpenMayaUI as OpenMayaUI  # pylint: disable=E0401

import RenderSetupUtility

from MayaCustomShelf.customCamera import CAMERA_TEMPLATE
from MayaCustomShelf.mayaViewportPreset import MAYA_VIEWPORT_PRESET
from MayaCustomShelf.mayaViewportPreset import applyViewportPreset
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
    """Separator."""
    pass


def reload_modules(f):
    """Reloads the given module name."""
    for module in sys.modules.values():
        if not module:
            continue
        elif f.lower() not in module.__name__.lower():
            continue
        try:
            imp.reload(module)
            print module, 'reloaded.'
        except ImportError as err:
            print err
        except TypeError as err:
            print err
        except RuntimeError as err:
            print err
        except AssertionError as err:
            print err


def rsUtility(*args):  # pylint: disable=W0613
    """Show RenderSetupUtility Window"""
    reload_modules('RenderSetupUtility')
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


def toggleFullScreen(*args):  # pylint: disable=W0613
    """This is a hackish implementation to toggle Maya's full-screen mode."""

    TEMPLATE = {
        'Shelf': True, # hide shelves
        'Outliner': False, # hide the outliner
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
        if not parent:
            return parent

        gparent = parent.parent()
        if gparent:
            return gparent
        return parent

    o = QGet()
    mode = True
    for k in TEMPLATE:
        item = getQt(k)
        if TEMPLATE[k] and item:
            mode = True if item.isHidden() else False
            break

    # Maya MainWindow children visibility
    if mode:
        o.mayaMainWindow.showMaximized()
        for k in TEMPLATE:
            item = getQt(k)
            if TEMPLATE[k] and item:
                item.show()
    else:
        o.mayaMainWindow.showFullScreen()
        for k in TEMPLATE:
            item = getQt(k)
            if TEMPLATE[k] and item:
                item.hide()

    # model editor icon bars
    for modelPanel in cmds.getPanel(type='modelPanel'):
        if modelPanel not in ['modelPanel1', 'modelPanel2', 'modelPanel3', 'modelPanel4']:
            continue

        ptr = OpenMayaUI.MQtUtil.findControl(modelPanel)
        if not ptr:
            continue

        widget = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
        iconbar = widget.findChildren(
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
        """ get mesh bounding box """

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
        cmds.polyMirrorFace(
            s,
            worldSpace=True,
            pivot=(0, 0, 0),
            mergeMode=MERGE_MODE,
            mergeThreshold=MERGE_THRESHOLD,
            direction=axis,
            constructionHistory=True
        )

    if hilite:
        cmds.hilite(hilite, replace=True)

    else:
        cmds.select(sel)

def unlock_attributes(obj):
    """Unlocks all the attributes of the given object."""
    attrs = cmds.listAttr(obj)
    for attr in attrs:
        try:
            if cmds.getAttr("{0}.{1}".format(obj, attr), lock=True) == True:
                print "{0}.{1} is Locked".format(obj, attr)
                cmds.setAttr("{0}.{1}".format(obj, attr), lock=False)
            else:
                print "{0}.{1} is unlocked".format(obj, attr)
        except ValueError:
            print "Couldn't get locked-state of {0}.{1}".format(obj, attr)

def resetMesh(*args):
    """Deletes the mesh construction history."""
    sel = cmds.ls(selection=True, long=True)
    for s in sel:
        unlock_attributes(s)
        cmds.cutKey(s, shape=True, hierarchy='both')
        cmds.makeIdentity(apply=True)
        cmds.delete(s, constructionHistory=True)

def showProjects(*args):
    """Shows the custom file-browser."""
    import browser.hosts.mayabrowser.mayabrowser as mayabrowser
    widget = mayabrowser.MayaBrowserWidget()
    widget.filesWidget.hide()
    widget.activate_widget(widget.projectsWidget)

def showFiles(*args):
    """Shows the custom file-browser."""
    import browser.hosts.mayabrowser.mayabrowser as mayabrowser
    widget = mayabrowser.MayaBrowserWidget()
    widget.projectsWidget.hide()
    widget.activate_widget(widget.filesWidget)


def randomizedDuplicate(*args):  # pylint: disable=W0613
    """Show the Random Duplicate UI"""
    RandomDuplicate().createUI()


def setMenuMode(arg):
    """Switch menu working mode"""
    s = '%sMenuSet' % (arg.lower())
    cmds.setMenuMode(s)


def createUI():
    """Main method to create the toolbar.

    We're using Maya's internal gui creation to make the toolbar,
    but perhaps this would be better implemented to be written in PySide2.

    """
    btnIdx = -1
    shelfIdx = -1
    btnCmds = []

    mayaMainWindow = shiboken2.wrapInstance(
        long(OpenMayaUI.MQtUtil.mainWindow()),
        QtWidgets.QWidget
    )

    try:
        cmds.deleteUI('%s' % (windowID))
        cmds.deleteUI('%s%s' % (windowID, 'WorkspaceControl'))
    except RuntimeError:
        print  'Object \'MayaCustomShelfWindow\' not found.'

    window = QtWidgets.QWidget()
    window.setObjectName(windowID)
    window.setFixedHeight(36)
    window.show()

    # The main layout. TODO: Would be cleaner if this was a PySide2 widget/layout
    shelfIdx += 1
    cmds.shelfLayout(
        '%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        parent=windowID,
        style='iconOnly',
        width=windowSize[0],
        height=32,
        cellWidthHeight=[windowSize[1] + margin[0]] * 2,
        preventOverride=True
    )

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
        command=rsUtility
    )
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=separator,
        enable=False
    )
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
        command=importCameraPresetScene
    )
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
        command=viewPreset1
    )
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
        command=viewPreset2
    )
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
        command=viewPreset3
    )
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
        command=toggleFullScreen
    )
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=separator,
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

    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=separator,
        enable=False
    )

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
        command=randomizedDuplicate
    )
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=separator,
        enable=False
    )
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
        command=resetMesh
    )
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=separator,
        enable=False
    )
    cmds.button(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='Shows the custom project browser...',
        width=windowSize[1] * 2,
        height=30,
        backgroundColor=[0.26, 0.26, 0.26],
        highlightColor=[0.78, 0.78, 0.78],
        align='center',
        label='Files',
        command=showFiles
    )
    cmds.button(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='Shows the custom project browser...',
        width=windowSize[1] * 2,
        height=30,
        backgroundColor=[0.26, 0.26, 0.26],
        highlightColor=[0.78, 0.78, 0.78],
        align='center',
        label='Projects',
        command=showProjects
    )
    cmds.shelfButton(
        parent='%s_%s%s' % (windowPrefix, 'shelfLayout', shelfIdx),
        annotation='',
        width=24,
        height=windowSize[1],
        image=getIconPath('separator16x32'),
        useAlpha=True,
        flat=True,
        sourceType='python',
        command=separator,
        enable=False
    )

    window.setContentsMargins(0, 0, 0, 0)
    window.layout().setContentsMargins(0, 0, 0, 0)
    window.layout().setSpacing(0)

    ptr = OpenMayaUI.MQtUtil.findControl('MainPane')
    widget = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
    widget.layout().insertWidget(0, window)
