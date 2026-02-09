import os
from collections import defaultdict

import FreeCAD as App
import FreeCADGui as Gui

from freecad.frameforge._utils import (
    is_extrudedcutout,
    is_fusion,
    is_group,
    is_part,
    is_profile,
    is_trimmedbody, 
    is_link,
    get_profiles_and_links_from_object
)


from freecad.frameforge.ff_tools import ICONPATH, PROFILEIMAGES_PATH, PROFILESPATH, UIPATH, translate




def place_balloon(balloon):
    view = balloon.SourceView
    obj = App.ActiveDocument.getObject(balloon.TargetName)
    P = obj.Shape.CenterOfGravity

    D = view.Direction.normalize()
    X = view.XDirection.normalize()
    Y = D.cross(X).normalize()

    C = view.getGeometricCenter()

    d = P.sub(C)
    x2d = d.dot(X) # * view.Scale
    y2d = d.dot(Y) # * view.Scale
    
    pageX = view.X.Value + x2d
    pageY = view.Y.Value + y2d

    balloon.OriginX = x2d
    balloon.OriginY = y2d

    balloon.X = x2d + 20
    balloon.Y = y2d + 20

    balloon.Text = obj.PID

	
def create_balloon(view, src_obj):
    doc = App.ActiveDocument
    page = None
    for obj in doc.Objects:
        if obj.TypeId == "TechDraw::DrawPage":
            if hasattr(obj, "Views"):
                for v in obj.Views:
                    if view == v:
                        page = obj
                        break
                    elif v.TypeId == "TechDraw::DrawProjGroup":
                        for vv in v.Views:
                            if view == vv:
                                page = obj
                                break
    if page is None:
        raise RuntimeError("Impossible de trouver la page contenant la vue")

    balloon = doc.addObject('TechDraw::DrawViewBalloon', f"Balloon_{src_obj.Label}")
    balloon.addProperty("App::PropertyString", "TargetName", "FrameForge", "Target Profile").TargetName = src_obj.Name
    balloon.SourceView = view
    page.addView(balloon)

    place_balloon(balloon)




class CreateBalloonsCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "create-balloons.svg"),
            "MenuText": translate("FrameForge", "Create Balloons"),
            "Accel": "M, B",
            "ToolTip": translate(
                "FrameForge",
                "<html><head/><body><p><b>Automatically Create balloons for selected Profiles/Links</b> \
                    <br><br> \
                    select profiles, links \
                    </p></body></html>",
            ),
        }

    def IsActive(self):
        if App.ActiveDocument:
            selection = Gui.Selection.getSelection()

            views = [s for s in selection if s.TypeId == "TechDraw::DrawProjGroupItem"]
            if len(views) != 1:
                return False

            objects = [
                    sel
                    for sel in selection if 
                    is_fusion(sel)
                    or is_part(sel)
                    or is_group(sel)
                    or is_profile(sel)
                    or is_trimmedbody(sel)
                    or is_extrudedcutout(sel)
                    or is_link(sel)
                ]

            if len(objects) <= 0:
                return False

            return True

        return False

    def Activated(self):
        selection = Gui.Selection.getSelection()

        views = [s for s in selection if s.TypeId == "TechDraw::DrawProjGroupItem"]
        objects = [
                sel
                for sel in selection if 
                is_fusion(sel)
                or is_part(sel)
                or is_group(sel)
                or is_profile(sel)
                or is_trimmedbody(sel)
                or is_extrudedcutout(sel)
                or is_link(sel)
            ]

        if len(objects) <= 0 or len(views) != 1:
            return

        view = views[0]


        App.ActiveDocument.openTransaction("Create Balloons")

        sel_profiles, sel_links = [], []
        for s in objects:
            get_profiles_and_links_from_object(sel_profiles, sel_links, s)
        

        ff_objects = sel_profiles + sel_links

        for o in ff_objects:
            create_balloon(view, o)


        App.ActiveDocument.commitTransaction()
        # App.ActiveDocument.recompute()




class ResfreshBalloonsCommand:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(ICONPATH, "refresh-balloons.svg"),
            "MenuText": translate("FrameForge", "Resfresh Balloons"),
            "Accel": "M, B",
            "ToolTip": translate(
                "FrameForge",
                "<html><head/><body><p><b>Refresh selected balloons</b> \
                    </p></body></html>",
            ),
        }

    def IsActive(self):
        if App.ActiveDocument:
            selection = Gui.Selection.getSelection()

            balloons = [b for b in selection if b.TypeId == "TechDraw::DrawViewBalloon" and hasattr(b, "TargetName")]
            if len(balloons) <= 0:
                return False
            return True

        return False

    def Activated(self):
        selection = Gui.Selection.getSelection()

        App.ActiveDocument.openTransaction("Resfresh Balloons")

        balloons = [b for b in selection if b.TypeId == "TechDraw::DrawViewBalloon" and hasattr(b, "TargetName")]
        for b in balloons:
            place_balloon(b)


        App.ActiveDocument.commitTransaction()
        # App.ActiveDocument.recompute()



Gui.addCommand("FrameForge_CreateBalloons", CreateBalloonsCommand())
Gui.addCommand("FrameForge_RefreshBalloons", ResfreshBalloonsCommand())
