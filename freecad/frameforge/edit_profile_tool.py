import glob
import json
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

from freecad.frameforge.create_profiles_tool import CreateProfileTaskPanel
from freecad.frameforge.profile import Profile, ViewProviderProfile


class EditProfileTaskPanel(CreateProfileTaskPanel):
    def __init__(self, profile):
        super().__init__()

        self.profile = profile
        self.dump = profile.dumpContent()

        # connect all the control to    slots that will update the profile...
        self.init_ui()

    def init_ui(self):
        self.form_proxy.groupBox_5.setEnabled(False)

        self.form_proxy.sb_width.setValue(self.profile.ProfileWidth)
        self.form_proxy.sb_height.setValue(self.profile.ProfileHeight)
        self.form_proxy.sb_main_thickness.setValue(self.profile.Thickness)
        self.form_proxy.sb_flange_thickness.setValue(self.profile.ThicknessFlange)
        self.form_proxy.sb_radius1.setValue(self.profile.RadiusLarge)
        self.form_proxy.sb_radius2.setValue(self.profile.RadiusSmall)
        self.form_proxy.sb_length.setValue(self.profile.ProfileLength)
        self.form_proxy.sb_weight.setValue(self.profile.ApproxWeight)
        self.form_proxy.cb_make_fillet.setChecked(self.profile.MakeFillet)
        self.form_proxy.cb_height_centered.setChecked(self.profile.CenteredOnHeight)
        self.form_proxy.cb_width_centered.setChecked(self.profile.CenteredOnWidth)

        self.form_proxy.combo_material.setCurrentText(self.profile.Material)
        self.form_proxy.combo_family.setCurrentText(self.profile.Family)
        self.form_proxy.combo_size.setCurrentText(self.profile.SizeName)

        # self.form_proxy.cb_combined_bevel.setChecked()

    def open(self):
        App.ActiveDocument.openTransaction("Edit Profile")

    def reject(self):
        self.profile.restoreContent(self.dump)
        Gui.ActiveDocument.resetEdit()

        App.ActiveDocument.commitTransaction()

        App.ActiveDocument.recompute()
        Gui.ActiveDocument.resetEdit()

        return True

    def accept(self):
        self.profile.Proxy.set_properties(
            self.profile,
            self.form_proxy.sb_width.value(),
            self.form_proxy.sb_height.value(),
            self.form_proxy.sb_main_thickness.value(),
            self.form_proxy.sb_flange_thickness.value(),
            self.form_proxy.sb_radius1.value(),
            self.form_proxy.sb_radius2.value(),
            self.form_proxy.sb_length.value(),
            self.form_proxy.sb_weight.value(),
            self.form_proxy.cb_make_fillet.isChecked(),  # and self.form_proxy.family.currentText() not in ["Flat Sections", "Square", "Round Bar"],
            self.form_proxy.cb_height_centered.isChecked(),
            self.form_proxy.cb_width_centered.isChecked(),
            self.form_proxy.combo_material.currentText(),
            self.form_proxy.combo_family.currentText(),
            self.form_proxy.combo_size.currentText(),
        )

        App.ActiveDocument.commitTransaction()

        App.ActiveDocument.recompute()
        Gui.ActiveDocument.resetEdit()

        return True
