import glob
import json
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, FormProxy, translate
from freecad.frameforge.profile import Profile, ViewProviderCustomProfile


class CreateCustomProfileTaskPanel:
    def __init__(self):
        self.form = Gui.PySideUic.loadUi(os.path.join(UIPATH, "create_custom_profiles.ui"))

        self.select_profile_flag = False
        self.custom_profile = None

        self.selection_list = []

        self.initialize_ui()

    def initialize_ui(self):
        self.form.pb_selectprofile.clicked.connect(self.select_profile)

    def open(self):
        self.update_selection()

        App.ActiveDocument.openTransaction("Add Custom Profile")

    def reject(self):
        self.clean()
        App.ActiveDocument.abortTransaction()

        return True

    def accept(self):
        if len(Gui.Selection.getSelectionEx()) or self.form.sb_length.value() > 0:
            self.proceed()
            self.clean()

            App.ActiveDocument.commitTransaction()
            App.ActiveDocument.recompute()

            return True

        else:
            diag = QtGui.QMessageBox(
                QtGui.QMessageBox.Warning, "Create Profile", "Select Edges or set Length to create a profile"
            )
            diag.setWindowModality(QtCore.Qt.ApplicationModal)
            diag.exec_()

            return False

    def clean(self):
        Gui.Selection.removeObserver(self)
        Gui.Selection.removeSelectionGate()

    def proceed(self):
        p_name = "Profile"
        if len(self.selection_list) == 1 and self.form.cb_sketch_in_name.isChecked():
            sketch_sel = self.selection_list[0]

            p_name += "_" + sketch_sel.Object.Name

        if self.form.cb_profile_in_name.isChecked():
            p_name += "_" + self.custom_profile.Label.replace(" ", "_")

        p_name += "_000"

        if len(self.selection_list):
            # create part or group and
            container = None
            if self.form.rb_profiles_in_part.isChecked():
                container = App.activeDocument().addObject("App::Part", "Part")
            # elif self.form.rb_profiles_in_group.isChecked(): # not working
            #     container = App.activeDocument().addObject('App::DocumentObjectGroup','Group')

            # creates profiles
            for sketch_sel in self.selection_list:
                # move the sketch inside the container
                if container:
                    container.addObject(sketch_sel.Object)

                if len(sketch_sel.SubElementNames) > 0:
                    edges = sketch_sel.SubElementNames
                else:  # use on the whole sketch
                    edges = [f"Edge{idx + 1}" for idx, e in enumerate(sketch_sel.Object.Shape.Edges)]

                for i, edge in enumerate(edges):
                    self.make_profile(sketch_sel.Object, edge, p_name)

        else:
            self.make_profile(None, None, p_name)

    def make_profile(self, sketch, edge, name):
        # Create an object in current document
        obj = App.ActiveDocument.addObject("Part::FeaturePython", name)
        obj.addExtension("Part::AttachExtensionPython")

        # move it to the sketch's parent if possible
        if sketch is not None and len(sketch.Parents) > 0:
            sk_parent = sketch.Parents[-1][0]
            sk_parent.addObject(obj)

        # Create a ViewObject in current GUI
        ViewProviderCustomProfile(obj.ViewObject)

        if sketch is not None and edge is not None:
            # Tuple assignment for edge
            feature = sketch
            link_sub = (feature, (edge))
            obj.MapMode = "NormalToEdge"

            try:
                obj.AttachmentSupport = (feature, edge)
            except AttributeError:  # for Freecad <= 0.21 support
                obj.Support = (feature, edge)

        else:
            link_sub = None

        obj.MapPathParameter = 1

        Profile(
            obj,
            0.0,  # self.form.sb_width.value(),
            0.0,  # self.form.sb_height.value(),
            0.0,  # self.form.sb_main_thickness.value(),
            0.0,  # self.form.sb_flange_thickness.value(),
            0.0,  # self.form.sb_radius1.value(),
            0.0,  # self.form.sb_radius2.value(),
            self.form.sb_length.value(),
            self.form.sb_weight.value(),
            0.0,  # init_unit_price (no UI in custom profile dialog)
            False,  # self.form.cb_make_fillet.isChecked(),  # and self.form.family.currentText() not in ["Flat Sections", "Square", "Round Bar"],
            1,  # self.form.cb_width_centered → center
            1,  # self.form.cb_height_centered → center
            self.form.le_material.text(),  # self.form.combo_material.currentText(),
            "Custom Profile",  # self.form.combo_family.currentText(),
            "None",  # self.form.combo_size.currentText(),
            False,  # self.form.cb_combined_bevel.isChecked(),
            link_sub,
            self.custom_profile,
            init_rotation=0.0,
        )

    def select_profile(self):
        if not self.select_profile_flag:
            self.select_profile_flag = True
            self.form.pb_selectprofile.setEnabled(False)
            self.form.pb_selectprofile.setText("Select a Profile")

    def addSelection(self, doc, obj, sub, other):
        if self.select_profile_flag:
            self.update_profile()

        else:
            self.update_selection()

    def clearSelection(self, other):
        if not self.select_profile_flag:
            self.update_selection()

    def update_profile(self):
        self.select_profile_flag = False
        self.form.pb_selectprofile.setEnabled(True)

        selection_list = Gui.Selection.getSelectionEx()
        if len(selection_list) == 1:
            profile_sel = selection_list[0]

            self.custom_profile = profile_sel.Object

            self.form.pb_selectprofile.setText(f"Profile {self.custom_profile.Label}")

        else:
            self.custom_profile = None
            self.form.pb_selectprofile.setText("Select Profile")

    def update_selection(self):
        # update internal list
        self.selection_list = Gui.Selection.getSelectionEx()

        if len(self.selection_list) > 0:
            self.form.sb_length.setEnabled(False)
            self.form.sb_length.setValue(0.0)

            obj_name = ""
            for sel in self.selection_list:
                selected_obj_name = sel.ObjectName
                subs = ""
                for sub in sel.SubElementNames:
                    subs += "{},".format(sub)

                obj_name += selected_obj_name
                obj_name += " / "
                obj_name += subs
                # obj_name += '\n'

        else:
            self.form.sb_length.setEnabled(True)
            obj_name = "Not Attached / Define length"

        self.form.label_attach.setText(obj_name)


class CreateCustomProfilesCommand:
    """Create Profiles with standards dimensions"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "warehouse_custom_profiles.svg"),
            "Accel": "Shift+C",  # a default shortcut (optional)
            "MenuText": "Create Custom Profile",
            "ToolTip": "Create new custom profiles from Edges",
        }

    def Activated(self):
        """Do something here"""
        panel = CreateCustomProfileTaskPanel()

        Gui.Selection.addObserver(panel)

        Gui.Control.showDialog(panel)

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return App.ActiveDocument is not None


Gui.addCommand("FrameForge_CreateCustomProfiles", CreateCustomProfilesCommand())
