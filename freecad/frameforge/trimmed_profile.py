import glob
import math
import os

import ArchCommands
import BOPTools.SplitAPI
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui

from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate


class TrimmedProfile:
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyLink", "TrimmedBody", "TrimmedProfile", translate("App::Property", "Body to be trimmed")
        ).TrimmedBody = None
        obj.addProperty(
            "App::PropertyLinkSubList",
            "TrimmingBoundary",
            "TrimmedProfile",
            translate("App::Property", "Bodies that define boundaries"),
        ).TrimmingBoundary = None

        obj.addProperty(
            "App::PropertyEnumeration",
            "TrimmedProfileType",
            "TrimmedProfile",
            translate("App::Property", "TrimmedProfile Type"),
        ).TrimmedProfileType = ["End Trim", "End Miter"]
        obj.addProperty(
            "App::PropertyEnumeration", "CutType", "TrimmedProfile", translate("App::Property", "Cut Type")
        ).CutType = [
            "Perfect fit",
            "Simple fit",
        ]

        obj.Proxy = self

    def onChanged(self, fp, prop):
        pass

    def execute(self, fp):
        """Print a short message when doing a recomputation, this method is mandatory"""
        App.Console.PrintMessage("Recompute {}\n".format(fp.Name))
        # TODO: Put these methods in proper functions
        if fp.TrimmedBody is None:
            return
        if len(fp.TrimmingBoundary) == 0:
            return

        cut_shapes = []

        if fp.TrimmedProfileType == "End Trim":
            if fp.CutType in ["Perfect fit", "Coped cut"]:  # Keeping Coped cut for retro-compatibility
                shapes = [x[0].Shape for x in fp.TrimmingBoundary]
                shps = BOPTools.SplitAPI.slice(fp.TrimmedBody.Shape, shapes, mode="Split")
                for solid in shps.Solids:
                    x = fp.TrimmedBody.Shape.CenterOfGravity.x
                    y = fp.TrimmedBody.Shape.CenterOfGravity.y
                    z = fp.TrimmedBody.Shape.CenterOfGravity.z
                    if not solid.BoundBox.isInside(x, y, z):
                        cut_shapes.append(Part.Shape(solid))

            elif fp.CutType in ["Simple fit", "Simple cut"]:  # Keeping Simple cut for retro-compatibility
                cut_shape = Part.Shape()
                for link in fp.TrimmingBoundary:
                    part = link[0]
                    for sub in link[1]:
                        face = part.getSubObject(sub)
                        if isinstance(face.Surface, Part.Plane):
                            shp = self.getOutsideCV(face, fp.TrimmedBody.Shape)
                            cut_shapes.append(shp)

        elif fp.TrimmedProfileType == "End Miter":
            doc = App.activeDocument()
            precision = 0.001
            target1 = self.getTarget(fp.TrimmedBody)
            edge1 = doc.getObject(target1[0].Name).getSubObject(target1[1][0])
            bounds_target = []
            for bound in fp.TrimmingBoundary:
                bounds_target.append(self.getTarget(bound[0]))
            trimming_boundary_edges = []
            for target in bounds_target:
                trimming_boundary_edges.append(doc.getObject(target[0].Name).getSubObject(target[1][0]))
            for edge2 in trimming_boundary_edges:
                end1 = edge1.Vertexes[-1].Point
                start1 = edge1.Vertexes[0].Point
                end2 = edge2.Vertexes[-1].Point
                start2 = edge2.Vertexes[0].Point
                vec1 = start1.sub(end1)
                vec2 = start2.sub(end2)

                angle = math.degrees(vec1.getAngle(vec2))

                if end1.distanceToPoint(start2) < precision or start1.distanceToPoint(end2) < precision:
                    angle = 180 - angle

                bisect = angle / 2.0

                if start1.distanceToPoint(start2) < precision:
                    p1 = start1
                    p2 = end1
                    p3 = end2
                elif start1.distanceToPoint(end2) < precision:
                    p1 = start1
                    p2 = end1
                    p3 = start2
                elif end1.distanceToPoint(start2) < precision:
                    p1 = end1
                    p2 = start1
                    p3 = end2
                elif end1.distanceToPoint(end2) < precision:
                    p1 = end1
                    p2 = start1
                    p3 = start2

                normal = Part.Plane(p1, p2, p3).toShape().normalAt(0, 0)
                cutplane = Part.makePlane(10, 10, p1, vec1, normal)
                cutplane.rotate(p1, normal, -90 + bisect)
                cut_shapes.append(self.getOutsideCV(cutplane, fp.TrimmedBody.Shape))

        if len(cut_shapes) > 0:
            cut_shape = Part.Shape(cut_shapes[0])
            for sh in cut_shapes[1:]:
                cut_shape = cut_shape.fuse(sh)

        self.makeShape(fp, cut_shape)

    def getOutsideCV(self, cutplane, shape):
        cv = ArchCommands.getCutVolume(cutplane, shape, clip=False, depth=0.0)
        if cv[1].isInside(shape.CenterOfGravity, 0.001, False):
            cv = cv[2]
        else:
            cv = cv[1]
        return cv

    def makeShape(self, fp, cutshape):
        if not cutshape.isNull():
            fp.Shape = fp.TrimmedBody.Shape.cut(cutshape)
        else:
            # TODO: Do something when cutshape is Null
            print("cut_shape is Null")

    def getTarget(self, link):
        while True:
            if hasattr(link, "Target"):
                return link.Target
            elif hasattr(link, "TrimmedProfileType"):
                link = link.TrimmedBody


class ViewProviderTrimmedProfile:
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
        # App.Console.PrintMessage("Change {} property: {}\n".format(str(fp), str(prop)))
        if prop == "TrimmedBody":
            if fp.TrimmedBody:
                self.ViewObject.ShapeColor = fp.TrimmedBody.ViewObject.ShapeColor
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
        childrens = [self.Object.TrimmedBody]
        if len(childrens) > 0:
            for child in childrens:
                if child:
                    # if hasattr("ViewObject", child)
                    child.ViewObject.Visibility = False
        return childrens

    def onChanged(self, vp, prop):
        """Print the name of the property that has changed"""
        # App.Console.PrintMessage("Change {} property: {}\n".format(str(vp), str(prop)))
        pass

    def onDelete(self, fp, sub):
        if self.Object.TrimmedBody:
            self.Object.TrimmedBody.ViewObject.Visibility = True
        return True

    def getIcon(self):
        """Return the icon in XMP format which will appear in the tree view. This method is optional
        and if not defined a default icon is shown.
        """
        return """
        	/* XPM */
                static char * corner_xpm[] = {
                "16 16 4 1",
                " 	c None",
                ".	c #000000",
                "+	c #3465A4",
                "@	c #ED2B00",
                "         ..     ",
                "       ..++..   ",
                "   .....+++++.  ",
                " ..@@@@@.+++... ",
                " .@.@@@@@.+.++. ",
                " .@@.@...@.+++. ",
                " .@@@.@@@@.+++. ",
                " .@@@.@@@@.+++. ",
                " ..@@.@@@@....  ",
                " .+.@.@@...     ",
                " .++....++.     ",
                " .+++.++++.     ",
                " .+++.++++.     ",
                "  .++.++++.     ",
                "   .+.+...      ",
                "    ...         "};
        	"""

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

        import freecad.frameforge.create_trimmed_profiles_tool

        taskd = freecad.frameforge.create_trimmed_profiles_tool.CreateTrimmedProfileTaskPanel(
            self.Object, mode="edition"
        )
        Gui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if mode != 0:
            return None

        Gui.Control.closeDialog()
        return True

    def edit(self):
        FreeCADGui.ActiveDocument.setEdit(self.Object, 0)
