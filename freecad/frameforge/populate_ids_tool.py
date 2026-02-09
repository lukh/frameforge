

#Expected behaviour:

# POPULATE
# Number/Letter for Profiles/Links
# - All numbers
# - All letters
# - Number for Profiles, Letters for Link
# - Number for Link, Letters for Profiles

# Allow duplicated numbering
# Keep existing

# Start at specific number/letter
# Fill when available (document)
# Fill when available (selection)
# Start at last of document


# Algorithm:

# - get all documents objects (flat)
# - get all selected objects (flat)


# RESET
# Reset All / Reset Selected if objects are selected




import os
from collections import defaultdict

import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge._utils import (
    is_extrudedcutout,
    is_fusion,
    is_group,
    is_part,
    is_profile,
    is_trimmedbody, 
    is_link,
    get_profiles_and_links_from_object, 
    get_profiles_and_links_from_document
)


from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate
from freecad.frameforge.populate_ids import populate_ids







class PopulateIDsTaskPanel:
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(os.path.join(UIPATH, "populate_ids.ui"))

        param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
        if not param.IsEmpty():
            self.form.cb_allow_duplicated.setChecked(param.GetBool("Allow Duplicating IDs", False))
            self.form.cb_reset_numbering.setChecked(param.GetBool("Reset Numbering IDs", False))
            self.form.cb_numbering_type.setCurrentIndex(param.GetInt("IDs numbering type", 0))
            self.form.cb_numbering_scheme.setCurrentIndex(param.GetInt("IDs numbering scheme", 0))
            self.form.sp_first_number.setValue(param.GetInt("First Number ID", 0))
            self.form.le_first_letter.setText(param.GetString("First Letter ID", "A"))

            

    def open(self):
        App.Console.PrintMessage(translate("frameforge", "Opening Populate IDs\n"))

        # create a TrimmedProfile object
        App.ActiveDocument.openTransaction("Populate IDs")

    def reject(self):
        App.Console.PrintMessage(translate("frameforge", "Rejecting Populate IDs\n"))

        self.clean()
        App.ActiveDocument.abortTransaction()

        return True

    def accept(self):
        sel = Gui.Selection.getSelection()

        if all(
                [
                    is_fusion(sel)
                    or is_part(sel)
                    or is_group(sel)
                    or is_profile(sel)
                    or is_trimmedbody(sel)
                    or is_extrudedcutout(sel)
                    or is_link(sel)
                    for sel in Gui.Selection.getSelection()
                ]
            ):
            param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
            param.SetBool("Allow Duplicating IDs", self.form.cb_allow_duplicated.isChecked())
            param.SetBool("Reset Numbering IDs", self.form.cb_reset_numbering.isChecked())
            param.SetInt("IDs numbering type", self.form.cb_numbering_type.currentIndex())
            param.SetInt("IDs numbering scheme", self.form.cb_numbering_scheme.currentIndex())

            param.SetInt("First Number ID", self.form.sp_first_number.value())
            param.SetString("First Letter ID", self.form.le_first_letter.text())

            sel_profiles, sel_links = [], []
            for s in sel:
                get_profiles_and_links_from_object(sel_profiles, sel_links, s)

            doc_profiles, doc_links = get_profiles_and_links_from_document()

            #handle compat here, Link don't have specific proxy
            for l in sel_links:
                if not hasattr(l, "PID"):
                    l.addProperty(
                        "App::PropertyString",
                        "PID",
                        "Frameforge",
                        "Profile ID",
                    ).PID = ""

                if not hasattr(l, "FrameforgeVersion"):
                    l.addProperty(
                        "App::PropertyString",
                        "FrameforgeVersion",
                        "Frameforge",
                        "Frameforge Version used to create the profile",
                    ).FrameforgeVersion = ff_version
                

            numbering_type = ["all_numbers", "all_letters", "number_for_profiles_letters_for_links" ,"letters_for_profiles_number_for_links"][self.form.cb_numbering_type.currentIndex()]
            allow_duplicated = self.form.cb_allow_duplicated.isChecked()
            reset_existing = self.form.cb_reset_numbering.isChecked()
            numbering_scheme = ["fill_selection", "fill_document", "continue_document", "start_at"][self.form.cb_numbering_scheme.currentIndex()]


            populate_ids(sel_profiles, sel_links, doc_profiles, doc_links, 
                numbering_type,
                allow_duplicated,
                reset_existing,
                numbering_scheme,
                start_number=str(self.form.sp_first_number.value()), start_letter=self.form.le_first_letter.text())


            App.ActiveDocument.commitTransaction()
            App.ActiveDocument.recompute()

            return True

        else:
            App.ActiveDocument.abortTransaction()
            return False

    def clean(self):
        pass







class PopulateIDsCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "populate-ids.svg"),
            "MenuText": translate("FrameForge", "Populate IDs"),
            "Accel": "M, B",
            "ToolTip": translate(
                "FrameForge",
                "<html><head/><body><p><b>Populate IDs of selected Frameforge objects</b> \
                    <br><br> \
                    select profiles, links or groups, parts \
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
                        for sel in Gui.Selection.getSelection()
                    ]
                )

        return False

    def Activated(self):
        panel = PopulateIDsTaskPanel()
        Gui.Control.showDialog(panel)




class ResetIDsCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "reset-ids.svg"),
            "MenuText": translate("FrameForge", "Reset IDs"),
            "Accel": "M, B",
            "ToolTip": translate(
                "FrameForge",
                "<html><head/><body><p><b>Reset IDs of selected Frameforge objects</b> \
                    <br><br> \
                    select profiles, links or groups, parts \
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
                        for sel in Gui.Selection.getSelection()
                    ]
                )

        return False

    def Activated(self):
        sel = Gui.Selection.getSelection()

        if all(
                [
                    is_fusion(sel)
                    or is_part(sel)
                    or is_group(sel)
                    or is_profile(sel)
                    or is_trimmedbody(sel)
                    or is_extrudedcutout(sel)
                    or is_link(sel)
                    for sel in Gui.Selection.getSelection()
                ]
            ):


            App.ActiveDocument.openTransaction("Reset IDs")
            sel_profiles, sel_links = [], []
            for s in sel:
                get_profiles_and_links_from_object(sel_profiles, sel_links, s)

            for o in sel_profiles+sel_links:
                o.PID = ""

            App.ActiveDocument.commitTransaction()
            App.ActiveDocument.recompute()
            

Gui.addCommand("FrameForge_PopulateIDs", PopulateIDsCommand())
Gui.addCommand("FrameForge_ResetIDs", ResetIDsCommand())


