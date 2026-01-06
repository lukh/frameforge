import os

import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge.create_bom import (
    is_extrudedcutout,
    is_fusion,
    is_group,
    is_part,
    is_profile,
    is_trimmedbody,
    make_bom,
)
from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate
from freecad.frameforge.trimmed_profile import TrimmedProfile, ViewProviderTrimmedProfile


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

        if all(
            [
                (
                    is_fusion(s)
                    or is_part(s)
                    or is_group(s)
                    or is_profile(s)
                    or is_trimmedbody(s)
                    or is_extrudedcutout(s)
                )
                for s in sel
            ]
        ):
            bom_name = self.form.bom_name_te.text() if self.form.bom_name_te.text() != "" else "BOM"
            make_bom(sel, bom_name=bom_name, group_profiles=self.form.group_profiles_cb.isChecked())

            App.ActiveDocument.commitTransaction()
            App.ActiveDocument.recompute()

            return True

        else:
            App.ActiveDocument.abortTransaction()
            return False

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
                return all(
                    [
                        is_fusion(sel)
                        or is_part(sel)
                        or is_group(sel)
                        or is_profile(sel)
                        or is_trimmedbody(sel)
                        or is_extrudedcutout(sel)
                        for sel in Gui.Selection.getSelection()
                    ]
                )

        return False

    def Activated(self):
        panel = CreateBOMTaskPanel()
        Gui.Control.showDialog(panel)


Gui.addCommand("FrameForge_CreateBOM", CreateBOMCommand())
