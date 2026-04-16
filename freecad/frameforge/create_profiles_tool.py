import glob
import json
import os
import re
from abc import ABC, abstractmethod

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui

from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, FormProxy, translate
from freecad.frameforge.profile import Profile, ViewProviderProfile


class BaseProfileTaskPanel(ABC):
    def __init__(self):
        self._objects = {}
        self._suspend_proceed = False

        self.form = [
            Gui.PySideUic.loadUi(os.path.join(UIPATH, "create_profiles1.ui")),
            Gui.PySideUic.loadUi(os.path.join(UIPATH, "create_profiles2.ui")),
        ]

        self.form_proxy = FormProxy(self.form)

        self.load_data()
        # self.initialize_ui() # Must be call in Child class, AFTER openTransaction

    def load_data(self):
        self.profiles = {}

        files = [f for f in os.listdir(PROFILESPATH) if f.endswith(".json")]

        for f in files:
            material_name = os.path.splitext(f)[0].capitalize()

            with open(os.path.join(PROFILESPATH, f)) as fd:
                self.profiles[material_name] = json.load(fd)

    def enable_signals(self, enable):
        # Block signals during initialization to prevent unintended side effects
        self.form_proxy.combo_material.blockSignals(not enable)
        self.form_proxy.combo_family.blockSignals(not enable)
        self.form_proxy.combo_size.blockSignals(not enable)

        self.form_proxy.sb_width.blockSignals(not enable)
        self.form_proxy.sb_height.blockSignals(not enable)
        self.form_proxy.sb_main_thickness.blockSignals(not enable)
        self.form_proxy.sb_flange_thickness.blockSignals(not enable)
        self.form_proxy.sb_radius1.blockSignals(not enable)
        self.form_proxy.sb_radius2.blockSignals(not enable)
        self.form_proxy.sb_length.blockSignals(not enable)
        self.form_proxy.cb_make_fillet.blockSignals(not enable)
        self.form_proxy.cb_mirror_h.blockSignals(not enable)
        self.form_proxy.cb_mirror_v.blockSignals(not enable)
        self.form_proxy.cb_pre_extend.blockSignals(not enable)
        self.form_proxy.combo_rotation.blockSignals(not enable)
        self.form_proxy.cb_sketch_in_name.blockSignals(not enable)
        self.form_proxy.cb_family_in_name.blockSignals(not enable)
        self.form_proxy.cb_size_in_name.blockSignals(not enable)
        self.form_proxy.cb_prefix_profile_in_name.blockSignals(not enable)
        for ax in range(3):
            for ay in range(3):
                getattr(self.form_proxy, f"rb_anchor_{ax}_{ay}").blockSignals(not enable)

    def request_proceed(self):
        if self._suspend_proceed:
            return
        self.proceed()

    def resolve_material_for_family(self, material, family, size_name=""):
        if material in self.profiles:
            return material
        matches = []
        for candidate, families in self.profiles.items():
            if family not in families:
                continue
            if size_name and size_name not in families[family]["sizes"]:
                continue
            matches.append(candidate)
        if len(matches) == 1:
            return matches[0]
        return None

    def populate_family_combo(self, material):
        self.form_proxy.combo_family.clear()
        self.form_proxy.combo_size.clear()
        if material not in self.profiles:
            return
        self.form_proxy.combo_family.addItems([f for f in self.profiles[material]])

    def populate_size_combo(self, material, family):
        self.form_proxy.combo_size.clear()
        if material not in self.profiles:
            return
        if family not in self.profiles[material]:
            return
        self.form_proxy.combo_size.addItems([s for s in self.profiles[material][family]["sizes"]])

    def initialize_ui(self, apply_defaults=True):
        def execute_if_has_bool(key, func):
            if key in [k for t, k, v in param.GetContents()]:
                func(param.GetBool(key))

        previous_suspend = self._suspend_proceed
        self._suspend_proceed = True

        # Center anchor radio buttons in grid cells (create_profiles2.ui)
        form2 = self.form[1]
        grid_anchor = form2.group_anchor.layout()
        for ax in range(3):
            for ay in range(3):
                btn = getattr(form2, f"rb_anchor_{ax}_{ay}")
                grid_anchor.setAlignment(btn, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.form_proxy.label_image.setPixmap(QtGui.QPixmap(os.path.join(PROFILEIMAGES_PATH, "Warehouse.png")))

        self.form_proxy.combo_material.addItems([k for k in self.profiles])

        for deg in ("0", "90", "180", "270"):
            self.form_proxy.combo_rotation.addItem(deg)
        self.form_proxy.combo_rotation.setCurrentIndex(0)

        self.form_proxy.combo_material.currentIndexChanged.connect(self.on_material_changed)
        self.form_proxy.combo_family.currentIndexChanged.connect(self.on_family_changed)
        self.form_proxy.combo_size.currentIndexChanged.connect(self.on_size_changed)
        self.on_material_changed(None)

        if apply_defaults:
            param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
            if not param.IsEmpty():
                default_material_index = self.form_proxy.combo_material.findText(
                    param.GetString("Default Profile Material")
                )
                if default_material_index > -1:
                    self.form_proxy.combo_material.setCurrentIndex(default_material_index)

                    default_family_index = self.form_proxy.combo_family.findText(
                        param.GetString("Default Profile Family")
                    )
                    if default_family_index > -1:
                        self.form_proxy.combo_family.setCurrentIndex(default_family_index)

                        default_size_index = self.form_proxy.combo_size.findText(
                            param.GetString("Default Profile Size")
                        )
                        if default_size_index > -1:
                            self.form_proxy.combo_size.setCurrentIndex(default_size_index)

                execute_if_has_bool("Default Sketch in Name", self.form_proxy.cb_sketch_in_name.setChecked)
                execute_if_has_bool("Default Family in Name", self.form_proxy.cb_family_in_name.setChecked)
                execute_if_has_bool("Default Size in Name", self.form_proxy.cb_size_in_name.setChecked)
                execute_if_has_bool(
                    "Default Prefix Profile in Name", self.form_proxy.cb_prefix_profile_in_name.setChecked
                )
                execute_if_has_bool("Default Make Fillet", self.form_proxy.cb_make_fillet.setChecked)
                execute_if_has_bool("Default Mirror Horizontally", self.form_proxy.cb_mirror_h.setChecked)
                execute_if_has_bool("Default Mirror Vertically", self.form_proxy.cb_mirror_v.setChecked)
                execute_if_has_bool("Default Pre Extend", self.form_proxy.cb_pre_extend.setChecked)
                keys = [k for t, k, v in param.GetContents()]
                if "Default AnchorX" in keys:
                    ax = max(0, min(2, param.GetInt("Default AnchorX", 1)))
                    ay = max(0, min(2, param.GetInt("Default AnchorY", 1)))
                    self.set_anchor(ax, ay)
                elif "Default Width Centered" in keys or "Default Height Centered" in keys:
                    ax = 1 if param.GetBool("Default Width Centered", False) else 0
                    ay = 1 if param.GetBool("Default Height Centered", False) else 0
                    self.set_anchor(ax, ay)
                if "Default RotationAngle" in keys:
                    try:
                        val = float(param.GetString("Default RotationAngle", "0"))
                        self.form_proxy.combo_rotation.setCurrentText(str(int(val) if val == int(val) else val))
                    except (TypeError, ValueError):
                        self.form_proxy.combo_rotation.setCurrentText("0")
                execute_if_has_bool("Default Centered Bevel", self.form_proxy.cb_combined_bevel.setChecked)

        self._suspend_proceed = previous_suspend

        self.form_proxy.cb_make_fillet.stateChanged.connect(self.on_cb_make_fillet_changed)

        self.form_proxy.cb_mirror_h.stateChanged.connect(self.request_proceed)
        self.form_proxy.cb_mirror_v.stateChanged.connect(self.request_proceed)
        self.form_proxy.cb_pre_extend.stateChanged.connect(self.request_proceed)
        self.form_proxy.combo_rotation.currentIndexChanged.connect(self.request_proceed)
        for ax in range(3):
            for ay in range(3):
                getattr(self.form_proxy, f"rb_anchor_{ax}_{ay}").clicked.connect(self.request_proceed)

        self.form_proxy.sb_width.valueChanged.connect(self.request_proceed)
        self.form_proxy.sb_height.valueChanged.connect(self.request_proceed)
        self.form_proxy.sb_main_thickness.valueChanged.connect(self.request_proceed)
        self.form_proxy.sb_flange_thickness.valueChanged.connect(self.request_proceed)
        self.form_proxy.sb_radius1.valueChanged.connect(self.request_proceed)
        self.form_proxy.sb_radius2.valueChanged.connect(self.request_proceed)
        self.form_proxy.sb_length.valueChanged.connect(self.request_proceed)

        self.form_proxy.cb_sketch_in_name.stateChanged.connect(self.request_proceed)
        self.form_proxy.cb_family_in_name.stateChanged.connect(self.request_proceed)
        self.form_proxy.cb_size_in_name.stateChanged.connect(self.request_proceed)
        self.form_proxy.cb_prefix_profile_in_name.stateChanged.connect(self.request_proceed)

    def get_anchor(self):
        """Return (anchor_x, anchor_y) 0=left/bottom, 1=center, 2=right/top."""
        for ax in range(3):
            for ay in range(3):
                if getattr(self.form_proxy, f"rb_anchor_{ax}_{ay}").isChecked():
                    return (ax, ay)
        return (1, 1)

    def set_anchor(self, anchor_x, anchor_y):
        ax = max(0, min(2, anchor_x))
        ay = max(0, min(2, anchor_y))
        getattr(self.form_proxy, f"rb_anchor_{ax}_{ay}").setChecked(True)

    def get_rotation(self):
        """Return rotation angle in degrees (float)."""
        try:
            return float(self.form_proxy.combo_rotation.currentText())
        except (TypeError, ValueError):
            return 0.0

    def set_rotation(self, degrees):
        t = str(int(degrees) if degrees == int(degrees) else degrees)
        i = self.form_proxy.combo_rotation.findText(t)
        if i >= 0:
            self.form_proxy.combo_rotation.setCurrentIndex(i)
        else:
            self.form_proxy.combo_rotation.setCurrentText(t)

    def on_material_changed(self, index):
        material = str(self.form_proxy.combo_material.currentText())
        previous_suspend = self._suspend_proceed
        self._suspend_proceed = True

        self.enable_signals(False)
        self.populate_family_combo(material)
        has_family = self.form_proxy.combo_family.count() > 0
        if has_family:
            self.form_proxy.combo_family.setCurrentIndex(0)
        self.enable_signals(True)
        self._suspend_proceed = previous_suspend

        if not has_family:
            return
        self.on_family_changed(None)

    def on_family_changed(self, index):
        material = str(self.form_proxy.combo_material.currentText())
        family = str(self.form_proxy.combo_family.currentText())
        previous_suspend = self._suspend_proceed
        self._suspend_proceed = True

        if material not in self.profiles:
            self.form_proxy.combo_size.clear()
            self._suspend_proceed = previous_suspend
            return
        if family not in self.profiles[material]:
            self.form_proxy.combo_size.clear()
            self._suspend_proceed = previous_suspend
            return

        self.enable_signals(False)
        self.form_proxy.cb_make_fillet.setChecked(self.profiles[material][family]["fillet"])
        self.form_proxy.cb_make_fillet.setEnabled(self.profiles[material][family]["fillet"])

        self.update_image()

        self.form_proxy.label_norm.setText(self.profiles[material][family]["norm"])
        self.form_proxy.label_unit.setText(self.profiles[material][family]["unit"])

        self.populate_size_combo(material, family)
        has_size = self.form_proxy.combo_size.count() > 0
        if has_size:
            self.form_proxy.combo_size.setCurrentIndex(0)
        self.enable_signals(True)
        self._suspend_proceed = previous_suspend

        if not has_size:
            return
        self.on_size_changed(None)

    def on_size_changed(self, index):
        material = str(self.form_proxy.combo_material.currentText())
        family = str(self.form_proxy.combo_family.currentText())
        size = str(self.form_proxy.combo_size.currentText())

        if material not in self.profiles:
            return
        if family not in self.profiles[material]:
            return
        if size not in self.profiles[material][family]["sizes"]:
            return

        if size != "":
            profile = self.profiles[material][family]["sizes"][size]

            SETTING_MAP = {
                "Height": self.form_proxy.sb_height,
                "Width": self.form_proxy.sb_width,
                "Thickness": self.form_proxy.sb_main_thickness,
                "Flange Thickness": self.form_proxy.sb_flange_thickness,
                "Radius1": self.form_proxy.sb_radius1,
                "Radius2": self.form_proxy.sb_radius2,
                "Weight": self.form_proxy.sb_weight,
            }

            self.enable_signals(False)

            self.form_proxy.sb_height.setEnabled(False)
            self.form_proxy.sb_height.setValue(0.0)
            self.form_proxy.sb_width.setEnabled(False)
            self.form_proxy.sb_width.setValue(0.0)
            self.form_proxy.sb_main_thickness.setEnabled(False)
            self.form_proxy.sb_main_thickness.setValue(0.0)
            self.form_proxy.sb_flange_thickness.setEnabled(False)
            self.form_proxy.sb_flange_thickness.setValue(0.0)
            self.form_proxy.sb_radius1.setEnabled(False)
            self.form_proxy.sb_radius1.setValue(0.0)
            self.form_proxy.sb_radius2.setEnabled(False)
            self.form_proxy.sb_radius2.setValue(0.0)
            self.form_proxy.sb_weight.setEnabled(False)
            self.form_proxy.sb_weight.setValue(0.0)

            for s in profile:
                if s == "Size":
                    continue

                if s not in SETTING_MAP:
                    raise ValueError("Setting Unkown")

                sb = SETTING_MAP[s]
                sb.setEnabled(True)

                sb.setValue(float(profile[s]))

            self.enable_signals(True)
            self.request_proceed()

    def on_cb_make_fillet_changed(self, state):
        self.update_image()
        self.request_proceed()

    def update_image(self):
        material = str(self.form_proxy.combo_material.currentText())
        family = str(self.form_proxy.combo_family.currentText())

        img_name = family.replace(" ", "_")
        if self.form_proxy.cb_make_fillet.isChecked():
            img_name += "_Fillet"
        img_name += ".png"

        self.form_proxy.label_image.setPixmap(QtGui.QPixmap(os.path.join(PROFILEIMAGES_PATH, material, img_name)))

    def update_profile(self, profile):
        offset = self.get_pre_extend_offset()
        profile.Proxy.set_properties(
            profile,
            self.form_proxy.sb_width.value(),
            self.form_proxy.sb_height.value(),
            self.form_proxy.sb_main_thickness.value(),
            self.form_proxy.sb_flange_thickness.value(),
            self.form_proxy.sb_radius1.value(),
            self.form_proxy.sb_radius2.value(),
            self.form_proxy.sb_length.value(),
            self.form_proxy.sb_weight.value(),
            self.form_proxy.sb_unitprice.value(),
            self.form_proxy.cb_make_fillet.isChecked(),  # and self.form_proxy.family.currentText() not in ["Flat Sections", "Square", "Round Bar"],
            *self.get_anchor(),
            self.form_proxy.combo_material.currentText(),
            self.form_proxy.combo_family.currentText(),
            self.form_proxy.combo_size.currentText(),
            init_mirror_h=self.form_proxy.cb_mirror_h.isChecked(),
            init_mirror_v=self.form_proxy.cb_mirror_v.isChecked(),
            init_rotation=self.get_rotation(),
            init_offset_a=offset,
            init_offset_b=offset,
        )

    def get_pre_extend_offset(self):
        if not self.form_proxy.cb_pre_extend.isChecked():
            return 0.0
        return max(self.form_proxy.sb_width.value(), self.form_proxy.sb_height.value())

    @abstractmethod
    def proceed(self):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def reject(self):
        return True

    @abstractmethod
    def accept(self):
        return True


class CreateProfileTaskPanel(BaseProfileTaskPanel):
    def __init__(self):
        super().__init__()

    def open(self):
        App.ActiveDocument.openTransaction("Add Profile")

        self.initialize_ui()

        self.update_selection()
        self.proceed()

    def reject(self):
        self.clean()

        App.ActiveDocument.abortTransaction()

        return True

    def accept(self):
        if len(Gui.Selection.getSelectionEx()) or self.form_proxy.sb_length.value() > 0:
            App.Console.PrintMessage(translate("frameforge", "Accepting CreateProfile\n"))

            param = App.ParamGet("User parameter:BaseApp/Preferences/Frameforge")
            param.SetString("Default Profile Material", self.form_proxy.combo_material.currentText())
            param.SetString("Default Profile Family", self.form_proxy.combo_family.currentText())
            param.SetString("Default Profile Size", self.form_proxy.combo_size.currentText())

            param.SetBool("Default Sketch in Name", self.form_proxy.cb_sketch_in_name.isChecked())
            param.SetBool("Default Family in Name", self.form_proxy.cb_family_in_name.isChecked())
            param.SetBool("Default Size in Name", self.form_proxy.cb_size_in_name.isChecked())
            param.SetBool("Default Prefix Profile in Name", self.form_proxy.cb_prefix_profile_in_name.isChecked())

            param.SetBool("Default Make Fillet", self.form_proxy.cb_make_fillet.isChecked())
            param.SetBool("Default Mirror Horizontally", self.form_proxy.cb_mirror_h.isChecked())
            param.SetBool("Default Mirror Vertically", self.form_proxy.cb_mirror_v.isChecked())
            param.SetBool("Default Pre Extend", self.form_proxy.cb_pre_extend.isChecked())

            ax, ay = self.get_anchor()
            param.SetInt("Default AnchorX", ax)
            param.SetInt("Default AnchorY", ay)
            param.SetString("Default RotationAngle", self.form_proxy.combo_rotation.currentText())
            param.SetBool("Default Centered Bevel", self.form_proxy.cb_combined_bevel.isChecked())

            param.RemBool("Default Reverse Attachement")

            self.proceed()
            self.clean()

            for o in self._objects.values():
                o.ViewObject.Transparency = 0
                o.ViewObject.ShapeColor = (0.44, 0.47, 0.5)

            App.ActiveDocument.commitTransaction()
            App.ActiveDocument.recompute()

            return True

        else:
            App.Console.PrintMessage(translate("frameforge", "Not Accepting CreateProfile\nSelect Edges or set Length"))

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
        seen_profiles = []

        selection_list = Gui.Selection.getSelectionEx()

        p_name = "Profile_" if self.form_proxy.cb_prefix_profile_in_name.isChecked() else ""

        if len(selection_list) == 1 and self.form_proxy.cb_sketch_in_name.isChecked():
            sketch_sel = selection_list[0]

            p_name += sketch_sel.Object.Name + "_"

        if self.form_proxy.cb_family_in_name.isChecked():
            p_name += self.form_proxy.combo_family.currentText().replace(" ", "_") + "_"

        if self.form_proxy.cb_size_in_name.isChecked():
            p_name += self.form_proxy.combo_size.currentText() + "_"

        p_name += "000"

        if len(selection_list):
            # create part or group and
            container = None
            if self.form_proxy.rb_profiles_in_part.isChecked():
                container = App.activeDocument().addObject("App::Part", "Part")
            # elif self.form_proxy.rb_profiles_in_group.isChecked(): # not working
            #     container = App.activeDocument().addObject('App::DocumentObjectGroup','Group')

            # creates profiles
            for sketch_sel in selection_list:
                # move the sketch inside the container
                if container:
                    container.addObject(sketch_sel.Object)

                if len(sketch_sel.SubElementNames) > 0:
                    edges = sketch_sel.SubElementNames
                else:  # use on the whole sketch
                    edges = [f"Edge{idx + 1}" for idx, e in enumerate(sketch_sel.Object.Shape.Edges)]

                for i, edge in enumerate(edges):
                    k = self.create_or_update_profile(sketch_sel.Object, edge, p_name)
                    seen_profiles.append(k)

        else:
            k = self.create_or_update_profile(None, None, p_name)
            seen_profiles.append(k)

        for k in list(self._objects.keys()):
            o = self._objects[k]

            if k in seen_profiles:
                o.recompute()

            else:
                App.ActiveDocument.removeObject(o.Name)
                del o

    def has_name_prefix(self, internal_name, target_str):
        pattern = r"\d+$"

        prefix_obj = re.sub(pattern, "", internal_name)
        prefix_target = re.sub(pattern, "", target_str)

        return prefix_obj == prefix_target

    def create_or_update_profile(self, sketch, edge, name):
        key = (sketch, edge)

        if key in self._objects:
            o = self._objects[key]
            if self.has_name_prefix(o.Name, name):
                self.update_profile(o)

            else:
                # handle renames
                App.ActiveDocument.removeObject(o.Name)
                o = self.make_profile(sketch, edge, name)
                self._objects[key] = o

        else:
            o = self.make_profile(sketch, edge, name)
            self._objects[key] = o

        return key

    def make_profile(self, sketch, edge, name):
        # Create an object in current document
        obj = App.ActiveDocument.addObject("Part::FeaturePython", name)
        obj.addExtension("Part::AttachExtensionPython")

        obj.ViewObject.Transparency = 80
        obj.ViewObject.ShapeColor = (0.0, 0.8, 0.0)

        # move it to the sketch's parent if possible
        if sketch is not None and len(sketch.Parents) > 0:
            sk_parent = sketch.Parents[-1][0]
            sk_parent.addObject(obj)

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

        init_offset = 0.0
        if self.form_proxy.cb_pre_extend.isChecked():
            init_offset = max(self.form_proxy.sb_width.value(), self.form_proxy.sb_height.value())

        obj.MapPathParameter = 1

        Profile(
            obj,
            self.form_proxy.sb_width.value(),
            self.form_proxy.sb_height.value(),
            self.form_proxy.sb_main_thickness.value(),
            self.form_proxy.sb_flange_thickness.value(),
            self.form_proxy.sb_radius1.value(),
            self.form_proxy.sb_radius2.value(),
            self.form_proxy.sb_length.value(),
            self.form_proxy.sb_weight.value(),
            self.form_proxy.sb_unitprice.value(),
            self.form_proxy.cb_make_fillet.isChecked(),  # and self.form_proxy.family.currentText() not in ["Flat Sections", "Square", "Round Bar"],
            *self.get_anchor(),
            self.form_proxy.combo_material.currentText(),
            self.form_proxy.combo_family.currentText(),
            self.form_proxy.combo_size.currentText(),
            self.form_proxy.cb_combined_bevel.isChecked(),
            link_sub,
            init_mirror_h=self.form_proxy.cb_mirror_h.isChecked(),
            init_mirror_v=self.form_proxy.cb_mirror_v.isChecked(),
            init_rotation=self.get_rotation(),
            init_offset_a=init_offset,
            init_offset_b=init_offset,
        )

        # Create a ViewObject in current GUI
        ViewProviderProfile(obj.ViewObject)

        return obj

    def addSelection(self, doc, obj, sub, other):
        self.update_selection()

    def clearSelection(self, other):
        self.update_selection()

    def update_selection(self):
        if len(Gui.Selection.getSelectionEx()) > 0:
            self.form_proxy.sb_length.setEnabled(False)
            self.form_proxy.sb_length.setValue(0.0)

            obj_name = ""
            for sel in Gui.Selection.getSelectionEx():
                selected_obj_name = sel.ObjectName
                subs = ""
                for sub in sel.SubElementNames:
                    subs += "{},".format(sub)

                obj_name += selected_obj_name
                obj_name += " / "
                obj_name += subs
                # obj_name += '\n'

        else:
            self.form_proxy.sb_length.setEnabled(True)
            obj_name = "Not Attached / Define length"

        self.form_proxy.label_attach.setText(obj_name)


class CreateProfilesCommand:
    """Create Profiles with standards dimensions"""

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "warehouse_profiles.svg"),
            "Accel": "Shift+S",  # a default shortcut (optional)
            "MenuText": "Create Profile",
            "ToolTip": "Create new profiles from Edges",
        }

    def Activated(self):
        """Do something here"""
        panel = CreateProfileTaskPanel()

        Gui.Selection.addObserver(panel)

        Gui.Control.showDialog(panel)

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        return App.ActiveDocument is not None


Gui.addCommand("FrameForge_CreateProfiles", CreateProfilesCommand())
