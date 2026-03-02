import glob
import json
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

from freecad.frameforge.create_profiles_tool import BaseProfileTaskPanel
from freecad.frameforge.profile import ANCHOR_X, ANCHOR_Y, Profile, ViewProviderProfile


class EditProfileTaskPanel(BaseProfileTaskPanel):
    def __init__(self, profile):
        self.profile = profile
        self.dump = profile.dumpContent()

        super().__init__()

        self.proceed()

    def initialize_ui(self):
        super().initialize_ui()

        self.form_proxy.groupBox_5.setEnabled(False)

        self.form_proxy.sb_width.setValue(self.profile.ProfileWidth)
        self.form_proxy.sb_height.setValue(self.profile.ProfileHeight)
        self.form_proxy.sb_main_thickness.setValue(self.profile.Thickness)
        self.form_proxy.sb_flange_thickness.setValue(self.profile.ThicknessFlange)
        self.form_proxy.sb_radius1.setValue(self.profile.RadiusLarge)
        self.form_proxy.sb_radius2.setValue(self.profile.RadiusSmall)
        self.form_proxy.sb_length.setValue(self.profile.ProfileLength)
        self.form_proxy.sb_weight.setValue(self.profile.ApproxWeight)
        try:
            self.form_proxy.sb_unitprice.setValue(self.profile.UnitPrice)
        except:
            App.Console.PrintMessage(f"Frameforge : can't find Unit Price for {self.profile.Label}\n")
        self.form_proxy.cb_make_fillet.setChecked(self.profile.MakeFillet)
        if hasattr(self.profile, "AnchorX"):
            ax = ANCHOR_X.index(self.profile.AnchorX) if self.profile.AnchorX in ANCHOR_X else 1
            ay = ANCHOR_Y.index(self.profile.AnchorY) if self.profile.AnchorY in ANCHOR_Y else 1
        else:
            ax = 1 if getattr(self.profile, "CenteredOnWidth", False) else 0
            ay = 1 if getattr(self.profile, "CenteredOnHeight", False) else 0
        self.set_anchor(ax, ay)
        self.set_rotation(getattr(self.profile, "RotationAngle", 0.0))
        self.form_proxy.cb_mirror_h.setChecked(getattr(self.profile, "MirrorH", False))
        self.form_proxy.cb_mirror_v.setChecked(getattr(self.profile, "MirrorV", False))

        self.form_proxy.combo_material.setCurrentText(self.profile.Material)
        self.form_proxy.combo_family.setCurrentText(self.profile.Family)
        self.form_proxy.combo_size.setCurrentText(self.profile.SizeName)

        # self.form_proxy.cb_combined_bevel.setChecked()

    def open(self):
        App.ActiveDocument.openTransaction("Edit Profile")

        self.profile.ViewObject.Transparency = 50
        self.profile.ViewObject.ShapeColor = (0.8, 0.2, 0.1)

    def reject(self):
        App.ActiveDocument.abortTransaction()

        return True

    def accept(self):
        self.proceed()

        self.profile.ViewObject.Transparency = 0
        self.profile.ViewObject.ShapeColor = (0.44, 0.47, 0.5)

        App.ActiveDocument.commitTransaction()
        App.ActiveDocument.recompute()

        return True

    def proceed(self):
        self.update_profile(self.profile)

        self.profile.recompute()
