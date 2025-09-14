import glob
import json
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

from freecad.frameforge import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, FrameForgeException
from freecad.frameforge._ui_utils import FormProxy
from freecad.frameforge.extrude_cutout import ExtrudedCutout, ViewProviderExtrudedCutout
from freecad.frameforge.translate_utils import translate


class CreateExtrudedCutoutTaskPanel:
    """TaskPanel pour FrameForge ExtrudedCutout (corrigé pour CutType)."""

    def __init__(self, obj):
        self.obj = obj

        self.cut_types = [
            "Through All",
            "Distance",
        ]

        self.form = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(self.form)

        layout.addWidget(QtGui.QLabel("Cut type"))
        self.comboCutType = QtGui.QComboBox()
        self.comboCutType.addItems(self.cut_types)
        try:
            current = str(self.obj.CutType)
            idx = self.cut_types.index(current)
        except Exception:
            idx = 0
        self.comboCutType.setCurrentIndex(idx)
        layout.addWidget(self.comboCutType)

        self.spinA = QtGui.QDoubleSpinBox()
        self.spinA.setRange(-1e6, 1e6)
        self.spinA.setDecimals(4)
        try:
            self.spinA.setValue(float(self.obj.ExtrusionLength1.Value))
        except Exception:
            try:
                self.spinA.setValue(float(self.obj.ExtrusionLength1))
            except Exception:
                self.spinA.setValue(500.0)

        layout.addWidget(QtGui.QLabel("Extrusion Length"))
        layout.addWidget(self.spinA)

        self.comboCutType.currentIndexChanged.connect(self.onCutTypeChanged)
        self.spinA.valueChanged.connect(self.onLengthAChanged)

        self.updateWidgetsVisibility()

    def onCutTypeChanged(self, idx):
        if 0 <= idx < len(self.cut_types):
            self.obj.CutType = self.cut_types[idx]
        else:
            self.obj.CutType = self.cut_types[0]
        self.updateWidgetsVisibility()

        self.obj.recompute()

    def onLengthAChanged(self, val):
        self.obj.ExtrusionLength = val
        self.obj.recompute()

    def updateWidgetsVisibility(self):
        """Afficher/masquer les widgets de longueur selon CutType selectionné."""
        ct = getattr(self.obj, "CutType", self.cut_types[0])
        self.spinA.setVisible(ct in ["Distance"])

    def open(self):
        App.Console.PrintMessage(translate("frameforge", "Opening Create Extrude Cutout\n"))

        App.ActiveDocument.openTransaction("Create Cutout")

    def accept(self):
        App.Console.PrintMessage(translate("frameforge", "Accepting Create Extrude Cutout\n"))
        try:
            if hasattr(self.obj, "Sketch") and self.obj.Sketch:
                try:
                    self.obj.Sketch.ViewObject.hide()
                except Exception:
                    pass
        except Exception:
            pass

        App.ActiveDocument.commitTransaction()
        App.ActiveDocument.recompute()

        return True

    def reject(self):
        App.Console.PrintMessage(translate("frameforge", "Rejecting Create Extrude Cutout\n"))
        App.ActiveDocument.abortTransaction()

        return True


class AddExtrudedCutoutCommandClass:
    """Add Extruded Cutout command."""

    def GetResources(self):
        return {
            # The name of a svg file available in the resources.
            "Pixmap": os.path.join(ICONPATH, "extrude-cutout.svg"),
            "MenuText": translate("FrameForge", "Extruded Cutout"),
            "Accel": "E, C",
            "ToolTip": translate(
                "FrameForge",
                "Extruded cutout from sketch extrusion\n"
                "1. Select a face of the sheet metal part (must not be the thickness face) and\n"
                "2. Select a sketch for the extruded cut (the sketch must be closed).\n"
                "3. Use Property editor to modify other parameters",
            ),
        }

    def Activated(self):
        """Create an Extruded Cutout object from user selections."""
        # Get the selected object and face.
        selection = Gui.Selection.getSelectionEx()[0]
        # When user select first the sketch
        if selection.Object.isDerivedFrom("Sketcher::SketchObject"):
            # Get selected sketch
            cutSketch = selection.Object
            # Check if we have any sub-objects (faces) selected.
            selection = Gui.Selection.getSelectionEx()[1]
            if len(selection.SubObjects) == 0:
                raise FrameForgeException("No face selected. Please select a face.")
            # Get selected object.
            selected_object = selection.Object
            # Get the selected face.
            selected_face = [selected_object, selection.SubElementNames[0]]
        # When user select first the object face.
        else:
            # Check if we have any sub-objects (faces) selected.
            if len(selection.SubObjects) == 0:
                raise FrameForgeException("No face selected. Please select a face.")
            # Get selected object.
            selected_object = selection.Object
            # Get the selected face.
            selected_face = [selected_object, selection.SubElementNames[0]]
            # Get selected sketch.
            selection = Gui.Selection.getSelectionEx()[1]
            cutSketch = selection.Object

        if cutSketch is None or not selected_object.Shape:
            raise FrameForgeException("Both a valid sketch and an object with a shape must be selected.")

        App.ActiveDocument.openTransaction("Create Cutout")
        obj = App.ActiveDocument.addObject("Part::FeaturePython", "ExtrudedCutout")
        obj.addExtension("Part::AttachExtensionPython")

        extrude_cutout = ExtrudedCutout(obj, cutSketch, selected_face)
        ViewProviderExtrudedCutout(obj.ViewObject)
        App.ActiveDocument.commitTransaction()

        obj.recompute()

        panel = CreateExtrudedCutoutTaskPanel(obj)
        Gui.Control.showDialog(panel)

    def IsActive(self):
        return len(Gui.Selection.getSelection()) == 2


Gui.addCommand("FrameForge_AddExtrudeCutout", AddExtrudedCutoutCommandClass())
