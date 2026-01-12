import os

import FreeCAD as App
import FreeCADGui as Gui

import AttachmentEditor.TaskAttachmentEditor as TaskAttachmentEditor


from freecad.frameforge._utils import getRootObject
from freecad.frameforge.ff_tools import ICONPATH

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
            "Pixmap": os.path.join(ICONPATH, "link.svg"),
            "MenuText": "Attached Link",
            "ToolTip": "Create a link with Attachment"
        }

    def IsActive(self):
        return bool(App.ActiveDocument) and bool(Gui.Selection.getSelection())

    def Activated(self):
        sel = Gui.Selection.getSelection()
        if not sel:
            return

        App.ActiveDocument.openTransaction("Create Links")
        roots = set()
        for obj in sel:
            roots.add(getRootObject(obj))

        for root in roots:
            link = makeLink(root)
            Gui.Control.showDialog(TaskAttachmentEditor.AttachmentEditorTaskPanel(link))
        App.ActiveDocument.commitTransaction()

Gui.addCommand("FrameForge_Link", LinkCommand())