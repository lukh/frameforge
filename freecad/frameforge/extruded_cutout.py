import glob
import math
import os

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui

from freecad.frameforge._utils import (
    get_childrens_from_extrudedcutout,
    get_profile_from_extrudedcutout,
    get_readable_cutting_angles,
    get_trimmed_profile_all_cutting_angles,
    get_trimmedprofile_from_extrudedcutout,
    length_along_normal,
)
from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate
from freecad.frameforge.frameforge_exceptions import FrameForgeException
from freecad.frameforge.version import __version__ as ff_version


class ExtrudedCutout:
    def __init__(self, obj, sketch, selected_face):
        """Initialize the parametric Sheet Metal Cut object and add
        properties.
        """

        obj.addProperty(
            "App::PropertyString",
            "FrameforgeVersion",
            "Profile",
            "Frameforge Version used to create the profile",
        ).FrameforgeVersion = ff_version

        obj.addProperty(
            "App::PropertyString",
            "PID",
            "Profile",
            "Profile ID",
        ).PID = ""
        obj.setEditorMode("PID", 1)

        obj.addProperty("App::PropertyLinkSub", "baseObject", "ExtrudedCutout", "SelectedFace").baseObject = (
            selected_face
        )

        obj.addProperty(
            "App::PropertyLink",
            "Sketch",
            "ExtrudedCutout",
            translate("FrameForge", "The sketch for the cut"),
        ).Sketch = sketch

        obj.addProperty(
            "App::PropertyLength",
            "ExtrusionLength",
            "ExtrudedCutout",
            translate("FrameForge", "Length of the extrusion direction 1"),
        ).ExtrusionLength = 500.0
        obj.setEditorMode("ExtrusionLength", 2)  # Hide by default

        # CutType property
        obj.addProperty(
            "App::PropertyEnumeration", "CutType", "ExtrudedCutout", translate("FrameForge", "Cut type")
        ).CutType = [
            "Through All",
            "Distance",
        ]
        obj.CutType = "Through All"

        # related to Profile
        obj.addProperty("App::PropertyString", "Family", "Profile", "")
        obj.setEditorMode("Family", 1)

        obj.addProperty("App::PropertyLink", "CustomProfile", "Profile", "Target profile").CustomProfile = None
        obj.setEditorMode("CustomProfile", 1)

        obj.addProperty("App::PropertyString", "SizeName", "Profile", "")
        obj.setEditorMode("SizeName", 1)

        obj.addProperty("App::PropertyString", "Material", "Profile", "")
        obj.setEditorMode("Material", 1)

        obj.addProperty("App::PropertyFloat", "ApproxWeight", "Base", "Approximate weight in Kilogram")
        obj.setEditorMode("ApproxWeight", 1)

        obj.addProperty("App::PropertyFloat", "Price", "Base", "Profile Price")
        obj.setEditorMode("Price", 1)

        # structure
        obj.addProperty("App::PropertyLength", "Width", "Structure", "Parameter for structure")
        obj.addProperty("App::PropertyLength", "Height", "Structure", "Parameter for structure")
        obj.addProperty("App::PropertyLength", "Length", "Structure", "Parameter for structure")
        obj.addProperty("App::PropertyBool", "Cutout", "Structure", "Has Cutout").Cutout = True
        obj.setEditorMode("Width", 1)  # user doesn't change !
        obj.setEditorMode("Height", 1)
        obj.setEditorMode("Length", 1)
        obj.setEditorMode("Cutout", 1)

        obj.addProperty(
            "App::PropertyString",
            "CuttingAngleA",
            "Structure",
            "Cutting Angle A",
        )
        obj.setEditorMode("CuttingAngleA", 1)
        obj.addProperty(
            "App::PropertyString",
            "CuttingAngleB",
            "Structure",
            "Cutting Angle B",
        )
        obj.setEditorMode("CuttingAngleB", 1)

        obj.Proxy = self

    def onChanged(self, fp, prop):
        """Respond to property changes."""
        if prop == "CutType":
            if fp.CutType == "Distance":
                fp.setEditorMode("ExtrusionLength", 0)  # Show
            else:
                fp.setEditorMode("ExtrusionLength", 2)  # Hide

    def execute(self, fp):
        """Perform the cut when the object is recomputed."""
        try:
            self.run_compatibility_migrations(fp)

            # Ensure the Sketch and baseObject properties are valid.
            if fp.Sketch is None or fp.baseObject is None:
                raise FrameForgeException("Both the Sketch and baseObject properties must be set.")

            # hide trimmed body
            for tb in get_childrens_from_extrudedcutout(fp.baseObject[0]):
                tb.ViewObject.Visibility = False

            cutSketch = fp.Sketch
            selected_object, face_name = fp.baseObject

            face_name = face_name[0]
            selected_face = selected_object.Shape.getElement(face_name)
            normal_vector = selected_face.normalAt(0, 0)

            if fp.CutType == "Distance":
                ExtLength = fp.ExtrusionLength.Value
            else:
                skCenter = cutSketch.Shape.BoundBox.Center
                objCenter = selected_object.Shape.BoundBox.Center
                distance = skCenter - objCenter
                TotalLength = selected_object.Shape.BoundBox.DiagonalLength + distance.Length

                ExtLength = TotalLength

            # Create face from sketch
            skWiresList = cutSketch.Shape.Wires
            myFacesList = []
            for wire in skWiresList:
                myFace = Part.Face(wire)
                myFacesList.append(myFace)

            compFaces = Part.Compound(myFacesList)

            # Extrusion
            extruded_shape = compFaces.extrude(-normal_vector * ExtLength)

            # Soustraction (Cut)
            cut_shape = selected_object.Shape.cut(extruded_shape)

            # Assigne la forme au FeaturePython
            fp.Shape = cut_shape

            self._update_structure_data(fp)

        except FrameForgeException as e:
            App.Console.PrintError(f"Error: {e}\n")

    def _update_structure_data(self, obj):
        prof = get_profile_from_extrudedcutout(obj)
        trim_prof = get_trimmedprofile_from_extrudedcutout(obj)
        if trim_prof:
            angles = get_trimmed_profile_all_cutting_angles(trim_prof)
        else:
            angles = ()

        obj.PID = prof.PID
        obj.Width = prof.ProfileWidth
        obj.Height = prof.ProfileHeight
        obj.Family = prof.Family
        obj.CustomProfile = prof.CustomProfile
        obj.SizeName = prof.SizeName
        obj.Material = prof.Material
        obj.ApproxWeight = prof.ApproxWeight
        obj.Price = prof.Price

        obj.Length = length_along_normal(trim_prof if trim_prof else prof)

        cut_angles = get_readable_cutting_angles(
            getattr(prof, "BevelACutY", "N/A"),
            getattr(prof, "BevelACutX", "N/A"),
            getattr(prof, "BevelBCutY", "N/A"),
            getattr(prof, "BevelBCutX", "N/A"),
            *angles,
        )

        obj.CuttingAngleA = cut_angles[0]
        obj.CuttingAngleB = cut_angles[1]

    def run_compatibility_migrations(self, obj):
        if not hasattr(obj, "FrameforgeVersion"):
            obj.baseObject[0].Proxy.execute(obj.baseObject[0])

            App.Console.PrintMessage(f"Frameforge::object migration : Migrate {obj.Label} to 0.1.8\n")

            # related to Profile
            obj.addProperty(
                "App::PropertyString",
                "PID",
                "Profile",
                "Profile ID",
            ).PID = ""
            obj.setEditorMode("PID", 1)

            obj.addProperty("App::PropertyString", "Family", "Profile", "")
            obj.setEditorMode("Family", 1)

            obj.addProperty("App::PropertyLink", "CustomProfile", "Profile", "Target profile").CustomProfile = None
            obj.setEditorMode("CustomProfile", 1)

            obj.addProperty("App::PropertyString", "SizeName", "Profile", "")
            obj.setEditorMode("SizeName", 1)

            obj.addProperty("App::PropertyString", "Material", "Profile", "")
            obj.setEditorMode("Material", 1)

            obj.addProperty("App::PropertyFloat", "ApproxWeight", "Base", "Approximate weight in Kilogram")
            obj.setEditorMode("ApproxWeight", 1)

            obj.addProperty("App::PropertyFloat", "Price", "Base", "Profile Price")
            obj.setEditorMode("Price", 1)

            # structure
            obj.addProperty("App::PropertyLength", "Width", "Structure", "Parameter for structure")
            obj.addProperty("App::PropertyLength", "Height", "Structure", "Parameter for structure")
            obj.addProperty("App::PropertyLength", "Length", "Structure", "Parameter for structure")
            obj.addProperty("App::PropertyBool", "Cutout", "Structure", "Has Cutout").Cutout = True
            obj.setEditorMode("Width", 1)  # user doesn't change !
            obj.setEditorMode("Height", 1)
            obj.setEditorMode("Length", 1)
            obj.setEditorMode("Cutout", 1)

            obj.addProperty(
                "App::PropertyString",
                "CuttingAngleA",
                "Structure",
                "Cutting Angle A",
            )
            obj.setEditorMode("CuttingAngleA", 1)
            obj.addProperty(
                "App::PropertyString",
                "CuttingAngleB",
                "Structure",
                "Cutting Angle B",
            )
            obj.setEditorMode("CuttingAngleB", 1)

            # add version
            obj.addProperty(
                "App::PropertyString",
                "FrameforgeVersion",
                "Profile",
                "Frameforge Version used to create the profile",
            ).FrameforgeVersion = ff_version


class ViewProviderExtrudedCutout:
    """Part WB style ViewProvider."""

    def __init__(self, obj):
        """Set this object to the proxy object of the actual view provider"""
        obj.Proxy = self

    def attach(self, vobj):
        """Setup the scene sub-graph of the view provider, this method is mandatory"""
        self.ViewObject = vobj
        self.Object = vobj.Object
        return

    def updateData(self, fp, prop):
        """If a property of the handled feature has changed we have the chance to handle this here"""
        return

    def getDisplayModes(self, obj):
        """Return a list of display modes."""
        modes = []
        return modes

    def getDefaultDisplayMode(self):
        """Return the name of the default display mode. It must be defined in getDisplayModes."""
        return "FlatLines"

    def setDisplayMode(self, mode):
        """Map the display mode defined in attach with those defined in getDisplayModes.
        Since they have the same names nothing needs to be done. This method is optional.
        """
        return mode

    def claimChildren(self):
        childrens = [self.Object.baseObject[0], self.Object.Sketch]
        if len(childrens) > 0:
            for child in childrens:
                if child:
                    # if hasattr("ViewObject", child)
                    child.ViewObject.Visibility = False
        return childrens

    def onChanged(self, vp, prop):
        pass

    def onDelete(self, fp, sub):
        if self.Object.baseObject:
            self.Object.baseObject[0].ViewObject.Visibility = True
        if self.Object.Sketch:
            self.Object.Sketch.ViewObject.Visibility = True
        return True

    def __getstate__(self):
        """When saving the document this object gets stored using Python's cPickle module.
        Since we have some un-pickable here -- the Coin stuff -- we must define this method
        to return a tuple of all pickable objects or None.
        """
        return None

    def __setstate__(self, state):
        """When restoring the pickled object from document we have the chance to set some
        internals here. Since no data were pickled nothing needs to be done here.
        """
        return None

    def setEdit(self, vobj, mode):
        if mode != 0:
            return None

        taskd = freecad.frameforge.create_extruded_cutout_tool.CreateExtrudedCutoutTaskPanel(self.Object)
        Gui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if mode != 0:
            return None

        Gui.Control.closeDialog()
        return True

    def edit(self):
        FreeCADGui.ActiveDocument.setEdit(self.Object, 0)

    def getIcon(self):
        return """
        /* XPM */
            static char *profile[] = {
            /* columns rows colors chars-per-pixel */
            "15 16 15 1 ",
            "  c None",
            ". c #343636",
            "X c #53595F",
            "o c #303A4E",
            "O c #2A4A73",
            "+ c #31465A",
            "@ c #615954",
            "# c #AC6F35",
            "$ c #FFC400",
            "% c None",
            "& c #315F9B",
            "* c #5E6D84",
            "= c #E2A19F",
            "- c #E5D8D6",
            "; c #B8ADAC",
            /* pixels */
            "               ",
            "      Xo.      ",
            "    .o&&&o.    ",
            "    oOO&&&OX   ",
            " .o.o&&OO&&Oo  ",
            " X-;+O+OOO+##. ",
            " X---;#oOO#$#  ",
            " X--==-ooO%$#  ",
            " X===--#o+%$#  ",
            " X=-=-=#+O%$#  ",
            " X=-===*&O%$@  ",
            " X====-@o+#o.  ",
            " .;-==-o XX    ",
            "  .@--;o       ",
            "    X*@X       ",
            "     ..        "
            };

        """
