# Parametric line
# Initial author : Christophe Grellier (Chris_G)
# LGPL 2.
# Parametric line between two vertexes.
# Select 2 vertexes in the 3D View and activate the tool.

import os
import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui

from freecad.frameforge import _utils
from freecad.frameforge import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, "line.svg")


class ParametricLine:
    """Creates a parametric line between two vertexes"""

    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Vertex1", "ParametricLine", "First Vertex")
        obj.addProperty("App::PropertyLinkSub", "Vertex2", "ParametricLine", "Second Vertex")
        obj.Proxy = self

    def execute(self, obj):
        v1 = _utils.getShape(obj, "Vertex1", "Vertex")
        v2 = _utils.getShape(obj, "Vertex2", "Vertex")
        if v1 and v2:
            ls = Part.LineSegment(v1.Point, v2.Point)
            obj.Shape = ls.toShape()
        else:
            App.Console.PrintError("{} broken !\n".format(obj.Label))


class ParametricLineViewProvider:
    def __init__(self, vobj):
        vobj.Proxy = self

    def getIcon(self):
        return TOOL_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return {"name": self.Object.Name}

    def __setstate__(self, state):
        self.Object = App.ActiveDocument.getObject(state["name"])
        return None


class CreateParametricLineCommand:
    """Creates a parametric line between two vertexes"""

    def make_parametric_line(self, source):
        line_object = App.ActiveDocument.addObject("Part::FeaturePython", "ParametricLine")

        ParametricLine(line_object)
        ParametricLineViewProvider(line_object.ViewObject)

        line_object.Vertex1 = source[0]
        line_object.Vertex2 = source[1]
        App.ActiveDocument.recompute()

    def Activated(self):
        verts = []
        sel = Gui.Selection.getSelectionEx()
        for selobj in sel:
            if selobj.HasSubObjects:
                for i in range(len(selobj.SubObjects)):
                    if isinstance(selobj.SubObjects[i], Part.Vertex):
                        verts.append((selobj.Object, selobj.SubElementNames[i]))
        if len(verts) == 2:
            self.make_parametric_line(verts)

    def IsActive(self):
        if App.ActiveDocument:
            verts = []
            sel = Gui.Selection.getSelectionEx()
            for selobj in sel:
                if selobj.HasSubObjects:
                    for i in range(len(selobj.SubObjects)):
                        if isinstance(selobj.SubObjects[i], Part.Vertex):
                            verts.append((selobj.Object, selobj.SubElementNames[i]))
            return len(verts) == 2
        else:
            return False

    def GetResources(self):
        return {
            "Pixmap": TOOL_ICON,
            "MenuText": "Create a Parametric Line",
            "ToolTip": "Create a Parametric Line from two Vertex<br><br>Select two vertex then run this command",
        }


Gui.addCommand("FrameForge_ParametricLine", CreateParametricLineCommand())
