import glob
import json
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

from freecad.frameforge import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH
from freecad.frameforge._ui_utils import FormProxy
from freecad.frameforge.extrude_cutout import ExtrudedCutout, ViewProviderExtrudedCutout
from freecad.frameforge.translate_utils import translate


from freecad.frameforge import FrameForgeException



class FrameForgeExtrudedCutoutTaskPanel:
    """TaskPanel pour FrameForge ExtrudedCutout (corrigé pour CutType)."""

    def __init__(self, obj):
        self.obj = obj

        # Liste des types (gardez-la synchronisée avec la définition de la propriété)
        self.cut_types = [
            "Two dimensions",
            "Symmetric",
            "Through everything both sides",
            "Through everything side 1",
            "Through everything side 2",
        ]

        # Widget principal
        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.form)

        # CutSide (Inside / Outside)
        cutsideBox = QtWidgets.QGroupBox("Cut Side")
        hbox = QtWidgets.QHBoxLayout(cutsideBox)
        self.radioInside = QtWidgets.QRadioButton("Inside")
        self.radioOutside = QtWidgets.QRadioButton("Outside")
        hbox.addWidget(self.radioInside)
        hbox.addWidget(self.radioOutside)
        layout.addWidget(cutsideBox)

        # CutType (Combo)
        layout.addWidget(QtWidgets.QLabel("Cut type"))
        self.comboCutType = QtWidgets.QComboBox()
        self.comboCutType.addItems(self.cut_types)
        # positionner l'index courant d'après la valeur courante de la propriété
        try:
            current = str(self.obj.CutType)
            idx = self.cut_types.index(current)
        except Exception:
            idx = 0
        self.comboCutType.setCurrentIndex(idx)
        layout.addWidget(self.comboCutType)

        # Extrusion lengths
        self.spinA = QtWidgets.QDoubleSpinBox()
        self.spinA.setRange(-1e6, 1e6)
        self.spinA.setDecimals(4)
        # essayer de récupérer la valeur (supporte PropertyLength avec .Value)
        try:
            self.spinA.setValue(float(self.obj.ExtrusionLength1.Value))
        except Exception:
            try:
                self.spinA.setValue(float(self.obj.ExtrusionLength1))
            except Exception:
                self.spinA.setValue(500.0)

        self.spinB = QtWidgets.QDoubleSpinBox()
        self.spinB.setRange(-1e6, 1e6)
        self.spinB.setDecimals(4)
        try:
            self.spinB.setValue(float(self.obj.ExtrusionLength2.Value))
        except Exception:
            try:
                self.spinB.setValue(float(self.obj.ExtrusionLength2))
            except Exception:
                self.spinB.setValue(500.0)

        layout.addWidget(QtWidgets.QLabel("Extrusion Length 1"))
        layout.addWidget(self.spinA)
        layout.addWidget(QtWidgets.QLabel("Extrusion Length 2"))
        layout.addWidget(self.spinB)

        # Refine
        self.checkRefine = QtWidgets.QCheckBox("Refine geometry")
        try:
            self.checkRefine.setChecked(bool(self.obj.Refine))
        except Exception:
            self.checkRefine.setChecked(False)
        layout.addWidget(self.checkRefine)



        # Connexions signaux
        self.radioInside.toggled.connect(self.onCutSideChanged)
        self.comboCutType.currentIndexChanged.connect(self.onCutTypeChanged)
        self.spinA.valueChanged.connect(self.onLengthAChanged)
        self.spinB.valueChanged.connect(self.onLengthBChanged)
        self.checkRefine.stateChanged.connect(self.onRefineChanged)
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)

        # Initialiser l’affichage des radios
        if getattr(self.obj, "CutSide", "Inside") == "Inside":
            self.radioInside.setChecked(True)
        else:
            self.radioOutside.setChecked(True)

        # Mettre à jour visibilité widgets selon CutType
        self.updateWidgetsVisibility()

    def onCutSideChanged(self, checked):
        self.obj.CutSide = "Inside" if self.radioInside.isChecked() else "Outside"
        try:
            self.obj.Document.recompute()
        except Exception:
            pass

    def onCutTypeChanged(self, idx):
        # idx → valeur via self.cut_types
        if 0 <= idx < len(self.cut_types):
            self.obj.CutType = self.cut_types[idx]
        else:
            self.obj.CutType = self.cut_types[0]
        self.updateWidgetsVisibility()
        try:
            self.obj.Document.recompute()
        except Exception:
            pass

    def onLengthAChanged(self, val):
        # Essayons de respecter PropertyLength : on assigne un float (FreeCAD convertira)
        try:
            self.obj.ExtrusionLength1 = val
        except Exception:
            try:
                self.obj.ExtrusionLength1 = FreeCAD.Units.Quantity(str(val))
            except Exception:
                pass
        try:
            self.obj.Document.recompute()
        except Exception:
            pass

    def onLengthBChanged(self, val):
        try:
            self.obj.ExtrusionLength2 = val
        except Exception:
            try:
                self.obj.ExtrusionLength2 = FreeCAD.Units.Quantity(str(val))
            except Exception:
                pass
        try:
            self.obj.Document.recompute()
        except Exception:
            pass

    def onRefineChanged(self, state):
        self.obj.Refine = bool(state)
        try:
            self.obj.Document.recompute()
        except Exception:
            pass

    def updateWidgetsVisibility(self):
        """Afficher/masquer les widgets de longueur selon CutType selectionné."""
        ct = getattr(self.obj, "CutType", self.cut_types[0])
        self.spinA.setVisible(ct in ["Two dimensions", "Symmetric"])
        self.spinB.setVisible(ct == "Two dimensions")

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

    def reject(self):
        App.Console.PrintMessage(translate("frameforge", "Rejecting Create Extrude Cutout\n"))
        App.ActiveDocument.abortTransaction()




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
            raise FrameForgeException(
                "Both a valid sketch and an object with a shape must be selected.")



        obj = App.ActiveDocument.addObject("Part::FeaturePython", "ExtrudedCutout")
        obj.addExtension("Part::AttachExtensionPython")

        ExtrudedCutout(obj, cutSketch, selected_face)
        ViewProviderExtrudedCutout(obj.ViewObject)


    def IsActive(self):
        return len(Gui.Selection.getSelection()) == 2


Gui.addCommand("FrameForge_AddExtrudeCutout", AddExtrudedCutoutCommandClass())