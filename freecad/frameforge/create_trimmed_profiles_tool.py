import os, glob
import json

from PySide import QtCore, QtGui

import FreeCADGui as Gui
import FreeCAD as App

import Part, ArchCommands
import BOPTools.SplitAPI

from freecad.frameforge.translate_utils import translate
from freecad.frameforge import PROFILESPATH, PROFILEIMAGES_PATH, ICONPATH, UIPATH

from freecad.frameforge.trimmed_profile import TrimmedProfile, ViewProviderTrimmedProfile




class CreateTrimmedProfileTaskPanel():
    def __init__(self, fp, mode):
        ui_file = os.path.join(UIPATH, "create_trimmed_profiles.ui")
        self.form = Gui.PySideUic.loadUi(ui_file)


        self.fp = fp
        self.dump = fp.dumpContent()
        self.mode=mode

        self.initialize_ui()
        self.update_view_and_model()


    def initialize_ui(self):
        add_icon = QtGui.QIcon(os.path.join(ICONPATH, "list-add.svg"))
        remove_icon = QtGui.QIcon(os.path.join(ICONPATH, "list-remove.svg"))
        coped_type_icon = QtGui.QIcon(os.path.join(ICONPATH, "corner-coped-type.svg"))
        simple_type_icon = QtGui.QIcon(os.path.join(ICONPATH, "corner-simple-type.svg"))

        QSize = QtCore.QSize(32, 32)

        self.form.rb_copedcut.setIcon(coped_type_icon)
        self.form.rb_copedcut.setIconSize(QSize)
        self.form.rb_copedcut.toggled.connect(lambda: self.update_cuttype("Coped cut"))

        self.form.rb_simplecut.setIcon(simple_type_icon)
        self.form.rb_simplecut.setIconSize(QSize)
        self.form.rb_simplecut.toggled.connect(lambda: self.update_cuttype("Simple cut"))

        param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
        if param.GetString("Default Cut Type") == "Coped cut":
            self.form.rb_copedcut.toggle()
        elif param.GetString("Default Cut Type") == "Simple cut":
            self.form.rb_simplecut.toggle()

        self.form.add_trimmed_object_button.setIcon(add_icon)
        self.form.add_boundary_button.setIcon(add_icon)
        self.form.remove_boundary_button.setIcon(remove_icon)

        self.form.add_trimmed_object_button.clicked.connect(self.set_trimmed_body)
        self.form.add_boundary_button.clicked.connect(self.add_trimming_bodies)
        self.form.remove_boundary_button.clicked.connect(self.remove_trimming_bodies)


    def update_cuttype(self, cuttype):
        self.fp.CutType = cuttype

        self.update_view_and_model()


    def set_trimmed_body(self):
        if len(Gui.Selection.getSelectionEx()) == 1:
            trimmed_body = Gui.Selection.getSelectionEx()[0].Object
            App.Console.PrintMessage(translate("frameforge", f"Set Trimmed body: {trimmed_body.Name}\n"))
            self.fp.TrimmedBody = trimmed_body

            if len(trimmed_body.Parents) > 0:
                trimmed_body.Parents[-1][0].addObject(self.fp)

        self.update_view_and_model()



    def add_trimming_bodies(self):
        App.Console.PrintMessage(translate("frameforge", "Add Trimming bodies...\n"))

        # It looks like the TrimmingBoundary list must be rebuilt, not working if trying to only append data..
        trimming_boundaries = [e for e in self.fp.TrimmingBoundary]

        for selObject in Gui.Selection.getSelectionEx():
            if all([tb != (selObject.Object, tuple(selObject.SubElementNames)) for tb in trimming_boundaries]):
                trimming_boundaries.append((selObject.Object, tuple(selObject.SubElementNames)))

                App.Console.PrintMessage(translate("frameforge", f"\tadd trimming body: {selObject.ObjectName}, {tuple(selObject.SubElementNames)}\n"))

            else:
                App.Console.PrintMessage(translate("frameforge", "Already a trimming body for this TrimmedBody\n"))


        self.fp.TrimmingBoundary = trimming_boundaries

        self.update_view_and_model()

    def remove_trimming_bodies(self):
        App.Console.PrintMessage(translate("frameforge", "Remove Trimming body\n"))

        selected_tb = [item.data(1) for item in self.form.boundaries_list_widget.selectedItems()]
        self.fp.TrimmingBoundary = [tb for tb in self.fp.TrimmingBoundary if tb not in selected_tb]

        self.update_view_and_model()



    def update_view_and_model(self):
        if self.fp.TrimmedBody is not None:
            self.form.trimmed_object_label.setText("{} ({})".format(self.fp.TrimmedBody.Label, self.fp.TrimmedBody.Name))
        else:
            self.form.trimmed_object_label.setText("Select...")

        self.form.boundaries_list_widget.clear()

        # if self.fp.TrimmingBoundary is not None and len(self.fp.TrimmingBoundary) > 0:
        for bound in self.fp.TrimmingBoundary:
            item = QtGui.QListWidgetItem()
            item.setText("{} ({} {})".format(bound[0].Label, bound[0].Name, ", ".join(bound[1])))
            item.setData(1, bound)
            self.form.boundaries_list_widget.addItem(item)


        self.fp.recompute()


    def open(self):
        App.Console.PrintMessage(translate("frameforge", "Opening Create Trimmed Profile\n"))
        App.ActiveDocument.openTransaction("Update Trim")


    def reject(self):
        App.Console.PrintMessage(translate("frameforge", f"Rejecting CreateProfile {self.mode}\n"))

        if self.mode == "edition":
            self.fp.restoreContent(self.dump)
            Gui.ActiveDocument.resetEdit()

        elif self.mode == "creation":
            trimmedBody = self.fp.TrimmedBody

            App.ActiveDocument.removeObject(self.fp.Name)

            if trimmedBody:
                trimmedBody.ViewObject.Visibility = True

        App.ActiveDocument.commitTransaction()

        App.ActiveDocument.recompute()
        Gui.ActiveDocument.resetEdit()

        return True


    def accept(self):
        App.Console.PrintMessage(translate("frameforge", "Accepting Create Trimmed Profile\n"))

        param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
        param.SetString("Default Cut Type", self.fp.CutType)


        App.ActiveDocument.commitTransaction()

        App.ActiveDocument.recompute()
        Gui.ActiveDocument.resetEdit()

        return True




class TrimProfileCommand():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "corner-end-trim.svg"),
            "MenuText": translate("MetalWB", "Trim Profile"),
            "Accel": "M, C",
            "ToolTip": translate("MetalWB", "<html><head/><body><p><b>Trim a profile</b> \
                    <br><br> \
                    Select a profile then another profile's faces. \
                    </p></body></html>"),
        }

    def IsActive(self):
        if App.ActiveDocument:
            if len(Gui.Selection.getSelection()) > 0:
                active = False
                for sel in Gui.Selection.getSelection():
                    if hasattr(sel, 'Target'):
                        active = True
                    elif hasattr(sel, 'TrimmedBody'):
                        active = True
                    else:
                        return False
                return active
            else:
                return True
        return False

    def Activated(self):
        # create a TrimmedProfile object
        sel = Gui.Selection.getSelectionEx()
        App.ActiveDocument.openTransaction("Make Trimmed Profile")
        if len(sel) == 0:
            trimmed_profile = self.make_trimmed_profile()
        elif len(sel) == 1:
            trimmed_profile = self.make_trimmed_profile(trimmedBody=sel[0].Object)
        elif len(sel) > 1 :
            trimmingboundary = []
            for selectionObject in sel[1:]:
                bound = (selectionObject.Object, selectionObject.SubElementNames)
                trimmingboundary.append(bound)
            trimmed_profile = self.make_trimmed_profile(trimmedBody=sel[0].Object, trimmingBoundary=trimmingboundary)
        App.ActiveDocument.commitTransaction()


        panel = CreateTrimmedProfileTaskPanel(trimmed_profile, mode="creation")
        Gui.Control.showDialog(panel)



    def make_trimmed_profile(self, trimmedBody=None, trimmingBoundary=None):
        doc = App.ActiveDocument

        trimmed_profile = doc.addObject("Part::FeaturePython","TrimmedProfile")

        if trimmedBody is not None and len(trimmedBody.Parents) > 0:
            trimmedBody.Parents[-1][0].addObject(trimmed_profile)

        TrimmedProfile(trimmed_profile)

        ViewProviderTrimmedProfile(trimmed_profile.ViewObject)
        trimmed_profile.TrimmedBody = trimmedBody
        trimmed_profile.TrimmingBoundary = trimmingBoundary

        trimmed_profile.TrimmedProfileType = "End Trim"

        # doc.recompute()
        return trimmed_profile

Gui.addCommand("FrameForge_TrimProfiles", TrimProfileCommand())
