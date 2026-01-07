import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge._utils import getRootObject

def makeLink(source):
    doc = App.ActiveDocument

    link = doc.addObject("App::Link", source.Name + "_Link")
    link.LinkedObject = source

    link.addExtension("Part::AttachExtensionPython")
    link.MapMode = "Deactivated"

    doc.recompute()
    return link


class LinkCommand:
    def GetResources(self):
        return {
            "MenuText": "Attached Link",
            "ToolTip": "Create a link with Attachment"
        }

    def IsActive(self):
        return bool(App.ActiveDocument) and bool(Gui.Selection.getSelection())

    def Activated(self):
        sel = Gui.Selection.getSelection()
        if not sel:
            return

        roots = set()
        for obj in sel:
            roots.add(getRootObject(obj))

        for root in roots:
            makeLink(root)

Gui.addCommand("FrameForge_Link", LinkCommand())