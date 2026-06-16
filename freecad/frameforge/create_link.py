import os

import AttachmentEditor.TaskAttachmentEditor as TaskAttachmentEditor
import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge._utils import getRootObject
from freecad.frameforge.ff_tools import ICONPATH
from freecad.frameforge.version import __version__ as ff_version


def makeLink(source):
    doc = App.ActiveDocument

    link = doc.addObject("App::Link", source.Label + "_Link")
    link.LinkedObject = source

    link.addExtension("Part::AttachExtensionPython")
    link.MapMode = "Deactivated"

    link.addProperty(
        "App::PropertyString",
        "FrameforgeVersion",
        "Frameforge",
        "Frameforge Version used to create the profile",
    ).FrameforgeVersion = ff_version

    link.addProperty(
        "App::PropertyString",
        "PID",
        "Frameforge",
        "Profile ID",
    ).PID = ""

    doc.recompute()
    return link


class LinkCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "link.svg"),
            "MenuText": "Attached Link",
            "ToolTip": "Create a link with Attachment",
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

            def task_callback_ok():
                # trying to move into the top level (ie, Part)
                att_sups = link.AttachmentSupport
                if len(att_sups) == 1:
                    att_sup = att_sups[0]
                    att_sup_obj = att_sup[0]
                    if hasattr(att_sup_obj, "Group") and hasattr(att_sup_obj, "addObject"): # is Part or Group
                        att_sup_obj.addObject(link)

            Gui.Control.showDialog(TaskAttachmentEditor.AttachmentEditorTaskPanel(link, callback_OK=task_callback_ok))

        App.ActiveDocument.commitTransaction()


Gui.addCommand("FrameForge_Link", LinkCommand())
