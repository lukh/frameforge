import os
from collections import defaultdict
import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge.create_bom import (
    is_extrudedcutout,
    is_fusion,
    is_group,
    is_part,
    is_profile,
    is_trimmedbody,
    traverse_assembly,
    sort_profiles,
    make_bom,
)
from freecad.frameforge.best_fit import CutPart, Stock, best_fit_decreasing
from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate
from freecad.frameforge.trimmed_profile import TrimmedProfile, ViewProviderTrimmedProfile



def make_cut_list(sorted_stocks, cutlist_name="CutList"):
    doc = App.ActiveDocument
    spreadsheet = doc.addObject("Spreadsheet::Sheet", cutlist_name)

    spreadsheet.set("A1", "Material")
    spreadsheet.set("B1", "Stock")
    spreadsheet.set("C1", "CutPart")
    spreadsheet.set("D1", "Length")
    spreadsheet.set("E1", "CutAngle1")
    spreadsheet.set("F1", "CutAngle2")
    spreadsheet.set("G1", "Quantity")

    row = 2

    for stocks in sorted_stocks:
        stock_idx = 0
        for stock in sorted_stocks[stocks]:
            cut_part_idx = 0
            for cut_part in stock.parts:
                prof = cut_part.obj
                if cut_part_idx == 0:
                    spreadsheet.set("A" + str(row), stocks + f" / used = {stock.used:.1f}, left = {stock.left:.1f}")

                spreadsheet.set("B" + str(row), str(stock_idx))
                spreadsheet.set("C" + str(row), prof["label"])
                spreadsheet.set("D" + str(row), str(prof["length"]))
                spreadsheet.set("E" + str(row), "'" + str(prof["cut_angle_1"]))
                spreadsheet.set("F" + str(row), "'" + str(prof["cut_angle_2"]))
                spreadsheet.set("G" + str(row), str(prof["quantity"]))

                row += 1
                cut_part_idx += 1

            stock_idx += 1


        row += 1

    row +=1
    spreadsheet.set("A" + str(row), "Stock statistics")
    spreadsheet.set("B" + str(row), "Length Used")
    spreadsheet.set("C" + str(row), "Stock Used")
    spreadsheet.set("D" + str(row), "Stock Count")
    row +=1
    for stocks in sorted_stocks:
        spreadsheet.set("A" + str(row), stocks)
        spreadsheet.set("B" + str(row), f"{sum([s.used for s in sorted_stocks[stocks]])}")
        spreadsheet.set("C" + str(row), f"{sum([s.length for s in sorted_stocks[stocks]])}")
        spreadsheet.set("D" + str(row), f"{len(sorted_stocks[stocks])}")

        row +=1


    row += 1
    spreadsheet.set("A" + str(row), "Legend")
    spreadsheet.set("A" + str(row+1), "*")
    spreadsheet.set("B" + str(row+1), "Angles 1 and 2 are rotated 90° along the edge")
    spreadsheet.set("A" + str(row+2), "-")
    spreadsheet.set("B" + str(row+2), "Angles 1 and 2 are cut in the same direction (no need to rotate the stock 180° when cutting)")
    spreadsheet.set("A" + str(row+3), "~")
    spreadsheet.set("B" + str(row+3), "Angle is calculated from a TrimmedProfile -> be careful to check length, angles and cut direction")
    spreadsheet.set("A" + str(row+4), "?")
    spreadsheet.set("B" + str(row+4), "Can't compute the angle, do it yourself !")
    


class CreateBOMTaskPanel:
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(os.path.join(UIPATH, "create_bom.ui"))

        param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
        if not param.IsEmpty():
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
            param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
            param.SetBool("Group BOM Items by Material/Size/Family", self.form.group_profiles_cb.isChecked())
            param.SetBool("Generate Cut List", self.form.cut_list_cb.isChecked())
            param.SetFloat("Stock Length", self.form.stock_length_sb.value())
            param.SetFloat("Kerf", self.form.kerf_sb.value())


            bom_name = self.form.bom_name_te.text() if self.form.bom_name_te.text() != "" else "BOM"

            profiles_data = []
            for obj in sel:
                traverse_assembly(profiles_data, obj)

            if self.form.group_profiles_cb.isChecked():
                bom_data = sort_profiles(profiles_data)
            else:
                bom_data = profiles_data

            # BOM
            make_bom(bom_data, bom_name=bom_name)

            # Cut List
            if self.form.cut_list_cb.isChecked():
                grouped_profiles = defaultdict(list)
                for p in profiles_data:
                    key = (p["family"], p["material"], p["size_name"])
                    grouped_profiles[key].append(p)

                sorted_stocks = {}
                for k, group in grouped_profiles.items():
                    parts = [CutPart(p['label'], float(p['length']), self.form.kerf_sb.value(), p) for p in list(group)]

                    sorted_stocks[f"{k[1]}_{k[0]}_{k[2]}"] = best_fit_decreasing(self.form.stock_length_sb.value(), parts)

                make_cut_list(sorted_stocks, bom_name + "_CutList")


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
