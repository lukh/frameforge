import os

import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH
from freecad.frameforge.translate_utils import translate
from freecad.frameforge.trimmed_profile import TrimmedProfile, ViewProviderTrimmedProfile

from freecad.frameforge.create_bom import make_bom


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
        # create a TrimmedProfile object
        sel = Gui.Selection.getSelection()
        App.ActiveDocument.openTransaction("Make BOM")

        make_bom(sel)

        App.ActiveDocument.commitTransaction()
        App.ActiveDocument.recompute()


Gui.addCommand("FrameForge_CreateBOM", CreateBOMCommand())
