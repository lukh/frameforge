import os
from collections import defaultdict

import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge._utils import (
    is_extrudedcutout,
    is_fusion,
    is_group,
    is_link,
    is_part,
    is_profile,
    is_trimmedbody,
)
from freecad.frameforge.best_fit import CutPart, Stock, best_fit_decreasing
from freecad.frameforge.create_bom import (
    group_links,
    group_profiles,
    make_bom,
    make_cut_list,
    traverse_assembly,
)
from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate
from freecad.frameforge.trimmed_profile import TrimmedProfile, ViewProviderTrimmedProfile


class CreateBOMTaskPanel:
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(os.path.join(UIPATH, "create_bom.ui"))

        param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
        if not param.IsEmpty():
            self.form.full_parent_path.setChecked(param.GetBool("Full Parent Path", False))
            self.form.include_links_cb.setChecked(param.GetBool("Include Links in BOM", False))
            self.form.group_profiles_cb.setChecked(param.GetBool("Group BOM Items by Material/Size/Family", False))
            self.form.cut_list_cb.setChecked(param.GetBool("Generate Cut List", False))
            self.form.stock_length_sb.setValue(param.GetFloat("Stock Length", 6000.0))
            self.form.kerf_sb.setValue(param.GetFloat("Kerf", 1.0))

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

        bom_spreadsheet = None
        cutlist_spreadsheet = None

        if len(sel) >= 2:
            if sel[0].TypeId == "Spreadsheet::Sheet":
                # TODO : WarningBox
                bom_spreadsheet = sel[0]

            if sel[1].TypeId == "Spreadsheet::Sheet":
                # TODO : WarningBox
                cutlist_spreadsheet = sel[1]

            sel = [s for s in sel if s.TypeId != "Spreadsheet::Sheet"]


        if all(
            [
                (
                    is_fusion(s)
                    or is_part(s)
                    or is_group(s)
                    or is_profile(s)
                    or is_trimmedbody(s)
                    or is_extrudedcutout(s)
                    or is_link(s)
                )
                for s in sel
            ]
        ):
            param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
            param.SetBool("Full Parent Path", self.form.full_parent_path.isChecked())
            param.SetBool("Include Links in BOM", self.form.include_links_cb.isChecked())
            param.SetBool("Group BOM Items by Material/Size/Family", self.form.group_profiles_cb.isChecked())
            param.SetBool("Generate Cut List", self.form.cut_list_cb.isChecked())
            param.SetFloat("Stock Length", self.form.stock_length_sb.value())
            param.SetFloat("Kerf", self.form.kerf_sb.value())

            if self.form.bom_name_te.text() != "":
                bom_name = self.form.bom_name_te.text()
            elif len(sel) == 1:
                bom_name = f"{sel[0].Label}_BOM"
            else:
                bom_name = "BOM"

            profiles_data = []
            links_data = []
            for obj in sel:
                traverse_assembly(
                    profiles_data, links_data, obj, full_parent_path=self.form.full_parent_path.isChecked()
                )

            if self.form.group_profiles_cb.isChecked():
                bom_data = group_profiles(profiles_data)
                links_data = group_links(links_data)
            else:
                bom_data = profiles_data

            if not self.form.include_links_cb.isChecked():
                links_data = []

            # BOM
            make_bom(bom_data, links_data, bom_name=bom_name, spreadsheet=bom_spreadsheet)

            # Cut List
            if self.form.cut_list_cb.isChecked():
                grouped_profiles = defaultdict(list)
                for p in profiles_data:
                    key = (p["family"], p["material"], p["size_name"])
                    grouped_profiles[key].append(p)

                sorted_stocks = {}
                for k, group in grouped_profiles.items():
                    parts = [CutPart(p["label"], float(p["length"]), self.form.kerf_sb.value(), p) for p in list(group)]

                    sorted_stocks[f"{k[1]}_{k[0]}_{k[2]}"] = best_fit_decreasing(
                        self.form.stock_length_sb.value(), parts
                    )

                make_cut_list(sorted_stocks, cutlist_name=bom_name + "_CutList", spreadsheet=cutlist_spreadsheet)

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
                    select fusions or profiles. First select existing BOM and cutlist to update existing spreadsheet \
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
                        or is_link(sel)
                        or sel.TypeId == "Spreadsheet::Sheet"
                        for sel in Gui.Selection.getSelection()
                    ]
                )

        return False

    def Activated(self):
        panel = CreateBOMTaskPanel()
        Gui.Control.showDialog(panel)


Gui.addCommand("FrameForge_CreateBOM", CreateBOMCommand())
