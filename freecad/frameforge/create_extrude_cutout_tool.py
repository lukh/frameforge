
###################################################################################################
# Gui code
###################################################################################################

if SheetMetalTools.isGuiLoaded():
    Gui = FreeCAD.Gui
    icons_path = SheetMetalTools.icons_path


    class SMExtrudedCutoutVP(SheetMetalTools.SMViewProvider):
        """Part WB style ViewProvider."""

        def getIcon(self):
            return os.path.join(icons_path, "SheetMetal_AddCutout.svg")

        def getTaskPanel(self, obj):
            return SMExtrudedCutoutTaskPanel(obj)


    class SMExtrudedCutoutPDVP(SMExtrudedCutoutVP):
        """Part Design WB style ViewProvider.

        Note:
            Backward compatibility only.

        """


    class SMExtrudedCutoutTaskPanel:
        """A TaskPanel for the SheetMetal Extruded Cutout."""

        def __init__(self, obj):
            self.obj = obj
            self.form = SheetMetalTools.taskLoadUI("ExtrudedCutoutPanel.ui")
            self.LengthAText = FreeCAD.Qt.translate("SheetMetal", "Side A Length")
            self.LengthText = FreeCAD.Qt.translate("SheetMetal", "Length")

            # Make sure all properties are added.
            obj.Proxy.addVerifyProperties(obj)

            self.updateDisplay()

            self.faceSelParams = SheetMetalTools.taskConnectSelectionSingle(self.form.pushFace,
                    self.form.txtFace, obj, "baseObject", ["Face"])
            self.sketchSelParams = SheetMetalTools.taskConnectSelectionSingle(self.form.pushSketch,
                    self.form.txtSketch, obj, "Sketch", ("Sketcher::SketchObject", []))
            self.form.groupCutSide.buttonToggled.connect(self.cutSideChanged)
            SheetMetalTools.taskConnectEnum(obj, self.form.comboCutoutType, "CutType",
                                            self.cutTypeChanged)
            SheetMetalTools.taskConnectSpin(obj, self.form.unitLengthA, "ExtrusionLength1")
            SheetMetalTools.taskConnectSpin(obj, self.form.unitLengthB, "ExtrusionLength2")
            SheetMetalTools.taskConnectSpin(obj, self.form.intImproveLevel, "ImproveLevel")
            SheetMetalTools.taskConnectCheck(obj, self.form.checkImprove, "ImproveCut",
                                             self.improveChanged)
            SheetMetalTools.taskConnectCheck(obj, self.form.checkRefine, "Refine")

        def updateDisplay(self):
            if self.obj.CutSide == "Inside":
                self.form.radioInside.setChecked(True)
            else:
                self.form.radioOutside.setChecked(True)
            self.updateWidgetsVisibility()

        def cutSideChanged(self, button, checked):
            if not checked:
                return
            self.obj.CutSide = "Inside" if button == self.form.radioInside else "Outside"
            self.obj.Document.recompute()

        def improveChanged(self, isImprove):
            self.form.frameImproveLevel.setVisible(isImprove)

        def updateWidgetsVisibility(self):
            self.form.frameSideA.setVisible(self.obj.CutType in ["Two dimensions", "Symmetric"])
            self.form.frameSideB.setVisible(self.obj.CutType == "Two dimensions")
            self.form.labelSideA.setText(
                self.LengthText if self.obj.CutType == "Symmetric" else self.LengthAText)

        def cutTypeChanged(self, value):
            self.updateWidgetsVisibility()

        def isAllowedAlterSelection(self):
            return True

        def isAllowedAlterView(self):
            return True

        def accept(self):
            SheetMetalTools.taskAccept(self)
            SheetMetalTools.taskSaveDefaults(self.obj, smExtrudedCutoutDefaultVars)
            self.obj.Sketch.ViewObject.hide()  # Hide sketch after click OK button
            return True

        def reject(self):
            SheetMetalTools.taskReject(self)


    class AddExtrudedCutoutCommandClass:
        """Add Extruded Cutout command."""

        def GetResources(self):
            return {
                    # The name of a svg file available in the resources.
                    "Pixmap": os.path.join(icons_path, "SheetMetal_AddCutout.svg"),
                    "MenuText": FreeCAD.Qt.translate("SheetMetal", "Extruded Cutout"),
                    "Accel": "E, C",
                    "ToolTip": FreeCAD.Qt.translate(
                        "SheetMetal",
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
                    raise SMException("No face selected. Please select a face.")
                # Get selected object.
                selected_object = selection.Object
                # Get the selected face.
                selected_face = [selected_object, selection.SubElementNames[0]]
            # When user select first the object face.
            else:
                # Check if we have any sub-objects (faces) selected.
                if len(selection.SubObjects) == 0:
                    raise SMException("No face selected. Please select a face.")
                # Get selected object.
                selected_object = selection.Object
                # Get the selected face.
                selected_face = [selected_object, selection.SubElementNames[0]]
                # Get selected sketch.
                selection = Gui.Selection.getSelectionEx()[1]
                cutSketch = selection.Object

            if cutSketch is None or not selected_object.Shape:
                raise SMException(
                    "Both a valid sketch and an object with a shape must be selected.")

            # Create and assign the ExtrudedCutout object.
            newObj, activeBody = SheetMetalTools.smCreateNewObject(selected_object,
                                                                   "ExtrudedCutout")
            if newObj is None:
                return
            ExtrudedCutout(newObj, cutSketch, selected_face)
            SMExtrudedCutoutVP(newObj.ViewObject)
            SheetMetalTools.smAddNewObject(selected_object, newObj, activeBody,
                                           SMExtrudedCutoutTaskPanel)

        def IsActive(self):
            return len(Gui.Selection.getSelection()) == 2


    Gui.addCommand("SheetMetal_AddCutout", AddExtrudedCutoutCommandClass())