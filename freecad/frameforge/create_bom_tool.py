import os

import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH
from freecad.frameforge.translate_utils import translate
from freecad.frameforge.trimmed_profile import TrimmedProfile, ViewProviderTrimmedProfile

from freecad.frameforge.create_bom import make_bom, is_fusion, is_profile, is_trimmedbody


class CreateBOMTaskPanel:
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(os.path.join(UIPATH, "create_bom.ui"))

    def open(self):
        App.Console.PrintMessage(translate("frameforge", "Opening CreateBOM\n"))

        # create a TrimmedProfile object
        App.ActiveDocument.openTransaction("Make BOM")


    def reject(self):
        App.Console.PrintMessage(translate("frameforge", "Rejecting CreateBOM\n"))

        self.clean()
        App.ActiveDocument.abortTransaction()

        return True

    def accept(self):
        sel = Gui.Selection.getSelection()

        if all([(is_fusion(s) or is_profile(s) or is_trimmedbody(s)) for s in sel]):
            bom_name = self.form.bom_name_te.text() if self.form.bom_name_te.text() != "" else "BOM"
            make_bom(sel, bom_name=bom_name , group_profiles=self.form.group_profiles_cb.isChecked())

            App.ActiveDocument.commitTransaction()
            App.ActiveDocument.recompute()

            return True

        else:
            App.ActiveDocument.abortTransaction()
            

    def clean(self):
        pass

        

        


class CreateBOMCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "bom.svg"),
            "MenuText": translate("MetalWB", "Create BOM"),
            "Accel": "M, B",
            "ToolTip": translate(
                "MetalWB",
                "<html><head/><body><p><b>Create Spreadsheet with profiles</b> \
                    <br><br> \
                    select fusions or profiles \
                    </p></body></html>",
            ),
        }

    def IsActive(self):
        if App.ActiveDocument:
            if len(Gui.Selection.getSelection()) >= 1:
                active = False
                for sel in Gui.Selection.getSelection():
                    if hasattr(sel, "Target"):
                        active = True
                    elif hasattr(sel, "TrimmedBody"):
                        active = True
                    elif sel.TypeId == "Part::MultiFuse":
                        active = True
                    else:
                        return False
                return active
        return False

    def Activated(self):
        panel = CreateBOMTaskPanel()
        Gui.Control.showDialog(panel)


Gui.addCommand("FrameForge_CreateBOM", CreateBOMCommand())
