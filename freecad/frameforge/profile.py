import math

import FreeCAD as App
import FreeCADGui as Gui
import Part

from freecad.frameforge.extrusions import (
    tslot20x20,
    tslot20x20_one_slot,
    tslot20x20_three_slot,
    tslot20x20_two_slot,
    tslot20x20_two_slot_opp,
    vslot20x20,
    vslot20x40,
    vslot20x60,
    vslot20x80,
)

# Global variable for a 3D float vector (used in Profile class)
vec = App.Base.Vector


class Profile:
    def __init__(
        self,
        obj,
        init_w,
        init_h,
        init_mt,
        init_ft,
        init_r1,
        init_r2,
        init_len,
        init_wg,
        init_mf,
        init_hc,
        init_wc,
        material,
        fam,
        size_name,
        bevels_combined,
        link_sub=None,
        custom_profile=None,
    ):
        """
        Constructor. Add properties to FreeCAD Profile object. Profile object have 11 nominal properties associated
        with initialization value 'init_w' to 'init_wc' : ProfileHeight, ProfileWidth, [...] CenteredOnWidth. Depending
        on 'bevels_combined' parameters, there is 4 others properties for bevels : BevelStartCut1, etc. Depending on
        'fam' parameter, there is properties specific to profile family.
        """

        self.Type = "Profile"

        obj.addProperty(
            "App::PropertyString",
            "Material",
            "Profile",
            "",
        ).Material = material
        obj.addProperty(
            "App::PropertyString",
            "Family",
            "Profile",
            "",
        ).Family = fam
        obj.addProperty(
            "App::PropertyString",
            "SizeName",
            "Profile",
            "",
        ).SizeName = size_name

        obj.addProperty(
            "App::PropertyFloat",
            "ProfileHeight",
            "Profile",
            "",
        ).ProfileHeight = init_h
        obj.addProperty("App::PropertyFloat", "ProfileWidth", "Profile", "").ProfileWidth = init_w
        obj.addProperty("App::PropertyFloat", "ProfileLength", "Profile", "").ProfileLength = init_len  # should it be ?

        obj.addProperty(
            "App::PropertyFloat", "Thickness", "Profile", "Thickness of all the profile or the web"
        ).Thickness = init_mt
        obj.addProperty(
            "App::PropertyFloat", "ThicknessFlange", "Profile", "Thickness of the flanges"
        ).ThicknessFlange = init_ft

        obj.addProperty("App::PropertyFloat", "RadiusLarge", "Profile", "Large radius").RadiusLarge = init_r1
        obj.addProperty("App::PropertyFloat", "RadiusSmall", "Profile", "Small radius").RadiusSmall = init_r2
        obj.addProperty(
            "App::PropertyBool", "MakeFillet", "Profile", "Whether to draw the fillets or not"
        ).MakeFillet = init_mf

        if not bevels_combined:
            obj.addProperty(
                "App::PropertyFloat", "BevelStartCut1", "Profile", "Bevel on First axle at the start of the profile"
            ).BevelStartCut1 = 0
            obj.addProperty(
                "App::PropertyFloat",
                "BevelStartCut2",
                "Profile",
                "Rotate the cut on Second axle at the start of the profile",
            ).BevelStartCut2 = 0
            obj.addProperty(
                "App::PropertyFloat", "BevelEndCut1", "Profile", "Bevel on First axle at the end of the profile"
            ).BevelEndCut1 = 0
            obj.addProperty(
                "App::PropertyFloat",
                "BevelEndCut2",
                "Profile",
                "Rotate the cut on Second axle at the end of the profile",
            ).BevelEndCut2 = 0
        if bevels_combined:
            obj.addProperty(
                "App::PropertyFloat", "BevelStartCut", "Profile", "Bevel at the start of the profile"
            ).BevelStartCut = 0
            obj.addProperty(
                "App::PropertyFloat", "BevelStartRotate", "Profile", "Rotate the second cut on Profile axle"
            ).BevelStartRotate = 0
            obj.addProperty(
                "App::PropertyFloat", "BevelEndCut", "Profile", "Bevel on First axle at the end of the profile"
            ).BevelEndCut = 0
            obj.addProperty(
                "App::PropertyFloat", "BevelEndRotate", "Profile", "Rotate the second cut on Profile axle"
            ).BevelEndRotate = 0

        obj.addProperty("App::PropertyFloat", "ApproxWeight", "Base", "Approximate weight in Kilogram").ApproxWeight = (
            init_wg * init_len / 1000
        )

        obj.addProperty(
            "App::PropertyBool", "CenteredOnHeight", "Profile", "Choose corner or profile centre as origin"
        ).CenteredOnHeight = init_hc
        obj.addProperty(
            "App::PropertyBool", "CenteredOnWidth", "Profile", "Choose corner or profile centre as origin"
        ).CenteredOnWidth = init_wc

        if fam == "UPE":
            obj.addProperty("App::PropertyBool", "UPN", "Profile", "UPE style or UPN style").UPN = False
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 4.57
        if fam == "UPN":
            obj.addProperty("App::PropertyBool", "UPN", "Profile", "UPE style or UPN style").UPN = True
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 4.57

        if fam == "IPE" or fam == "HEA" or fam == "HEB" or fam == "HEM":
            obj.addProperty("App::PropertyBool", "IPN", "Profile", "IPE/HEA style or IPN style").IPN = False
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 8
        if fam == "IPN":
            obj.addProperty("App::PropertyBool", "IPN", "Profile", "IPE/HEA style or IPN style").IPN = True
            obj.addProperty("App::PropertyFloat", "FlangeAngle", "Profile").FlangeAngle = 8

        obj.addProperty("App::PropertyLength", "Width", "Structure", "Parameter for structure").Width = (
            obj.ProfileWidth
        )  # Property for structure
        obj.addProperty("App::PropertyLength", "Height", "Structure", "Parameter for structure").Height = (
            obj.ProfileLength
        )  # Property for structure
        obj.addProperty(
            "App::PropertyLength",
            "Length",
            "Structure",
            "Parameter for structure",
        ).Length = obj.ProfileHeight  # Property for structure
        obj.setEditorMode("Width", 1)  # user doesn't change !
        obj.setEditorMode("Height", 1)
        obj.setEditorMode("Length", 1)

        obj.addProperty("App::PropertyFloat", "OffsetA", "Structure", "Parameter for structure").OffsetA = (
            0.0  # Property for structure
        )

        obj.addProperty("App::PropertyFloat", "OffsetB", "Structure", "Parameter for structure").OffsetB = (
            0.0  # Property for structure
        )

        if link_sub:
            obj.addProperty("App::PropertyLinkSub", "Target", "Base", "Target face").Target = link_sub
            obj.setExpression(".AttachmentOffset.Base.z", "-OffsetA")

        if custom_profile:
            obj.addProperty("App::PropertyLink", "CustomProfile", "Base", "Target profile").CustomProfile = (
                custom_profile
            )
            obj.Family = "Custom Profile"

        self.WM = init_wg

        self.bevels_combined = bevels_combined
        obj.Proxy = self

    def set_properties(
        self,
        obj,
        init_w,
        init_h,
        init_mt,
        init_ft,
        init_r1,
        init_r2,
        init_len,
        init_wg,
        init_mf,
        init_hc,
        init_wc,
        material,
        fam,
        size_name,
    ):

        obj.Material = material
        obj.Family = fam
        obj.SizeName = size_name

        obj.ProfileHeight = init_h
        obj.ProfileWidth = init_w
        obj.ProfileLength = init_len  # should it be ?

        obj.Thickness = init_mt
        obj.ThicknessFlange = init_ft

        obj.RadiusLarge = init_r1
        obj.RadiusSmall = init_r2
        obj.MakeFillet = init_mf

        # if not bevels_combined:
        #     obj.BevelStartCut1", "Profile",
        #                     "Bevel on First axle at the start of the profile").BevelStartCut1 = 0
        #     obj.BevelStartCut2", "Profile",
        #                     "Rotate the cut on Second axle at the start of the profile").BevelStartCut2 = 0
        #     obj.BevelEndCut1", "Profile",
        #                     "Bevel on First axle at the end of the profile").BevelEndCut1 = 0
        #     obj.BevelEndCut2", "Profile",
        #                     "Rotate the cut on Second axle at the end of the profile").BevelEndCut2 = 0
        # if bevels_combined:
        #     obj.BevelStartCut", "Profile",
        #                     "Bevel at the start of the profile").BevelStartCut = 0
        #     obj.BevelStartRotate", "Profile",
        #                     "Rotate the second cut on Profile axle").BevelStartRotate = 0
        #     obj.BevelEndCut", "Profile",
        #                     "Bevel on First axle at the end of the profile").BevelEndCut = 0
        #     obj.BevelEndRotate", "Profile",
        #                     "Rotate the second cut on Profile axle").BevelEndRotate = 0

        obj.ApproxWeight = init_wg * init_len / 1000

        obj.CenteredOnHeight = init_hc
        obj.CenteredOnWidth = init_wc

        if obj.Family == "UPE":
            obj.UPN = False
            obj.FlangeAngle = 4.57
        if obj.Family == "UPN":
            obj.UPN = True
            obj.FlangeAngle = 4.57

        if obj.Family == "IPE" or obj.Family == "HEA" or obj.Family == "HEB" or obj.Family == "HEM":
            obj.IPN = False
            obj.FlangeAngle = 8
        if obj.Family == "IPN":
            obj.IPN = True
            obj.FlangeAngle = 8

        obj.Width = obj.ProfileWidth  # Property for structure
        obj.Height = obj.ProfileLength  # Property for structure
        obj.Length = obj.ProfileHeight  # Property for structure

        # obj.OffsetA = .0  # Property for structure
        # obj.OffsetB = .0  # Property for structure

    def on_changed(self, obj, p):

        if (
            p == "ProfileWidth"
            or p == "ProfileHeight"
            or p == "Thickness"
            or p == "FilletRadius"
            or p == "Centered"
            or p == "Length"
            or p == "BevelStartCut1"
            or p == "BevelEndCut1"
            or p == "BevelStartCut2"
            or p == "BevelEndCut2"
            or p == "BevelStartCut"
            or p == "BevelEndCut"
            or p == "BevelStartRotate"
            or p == "BevelEndRotate"
            or p == "OffsetA"
            or p == "OffsetB"
        ):
            self.execute(obj)

    def execute(self, obj):
        if not hasattr(obj, "Family"):  # for compat
            obj.addProperty(
                "App::PropertyString",
                "Family",
                "Profile",
                "",
            ).Family = self.fam

        try:
            L = obj.Target[0].getSubObject(obj.Target[1][0]).Length
            L += obj.OffsetA + obj.OffsetB
            obj.ProfileLength = L
        except:
            L = obj.ProfileLength + obj.OffsetA + obj.OffsetB

        obj.ApproxWeight = self.WM * L / 1000
        W = obj.ProfileWidth
        H = obj.ProfileHeight
        obj.Height = L
        pl = obj.Placement
        TW = obj.Thickness
        TF = obj.ThicknessFlange

        R = obj.RadiusLarge
        r = obj.RadiusSmall
        d = vec(0, 0, 1)

        w = h = 0

        if self.bevels_combined == False:
            if obj.BevelStartCut1 > 60:
                obj.BevelStartCut1 = 60
            if obj.BevelStartCut1 < -60:
                obj.BevelStartCut1 = -60
            if obj.BevelStartCut2 > 60:
                obj.BevelStartCut2 = 60
            if obj.BevelStartCut2 < -60:
                obj.BevelStartCut2 = -60

            if obj.BevelEndCut1 > 60:
                obj.BevelEndCut1 = 60
            if obj.BevelEndCut1 < -60:
                obj.BevelEndCut1 = -60
            if obj.BevelEndCut2 > 60:
                obj.BevelEndCut2 = 60
            if obj.BevelEndCut2 < -60:
                obj.BevelEndCut2 = -60

            B1Y = obj.BevelStartCut1
            B2Y = -obj.BevelEndCut1
            B1X = -obj.BevelStartCut2
            B2X = obj.BevelEndCut2
            B1Z = 0
            B2Z = 0

        if self.bevels_combined == True:
            if obj.BevelStartCut > 60:
                obj.BevelStartCut = 60
            if obj.BevelStartCut < -60:
                obj.BevelStartCut = -60
            if obj.BevelStartRotate > 60:
                obj.BevelStartRotate = 60
            if obj.BevelStartRotate < -60:
                obj.BevelStartRotate = -60

            if obj.BevelEndCut > 60:
                obj.BevelEndCut = 60
            if obj.BevelEndCut < -60:
                obj.BevelEndCut = -60
            if obj.BevelEndRotate > 60:
                obj.BevelEndRotate = 60
            if obj.BevelEndRotate < -60:
                obj.BevelEndRotate = -60

            B1Y = obj.BevelStartCut
            B1Z = -obj.BevelStartRotate
            B2Y = -obj.BevelEndCut
            B2Z = -obj.BevelEndRotate
            B1X = 0
            B2X = 0

        if obj.CenteredOnWidth == True:
            w = -W / 2
        if obj.CenteredOnHeight == True:
            h = -H / 2

        if obj.Family == "Equal Leg Angles" or obj.Family == "Unequal Leg Angles":
            if obj.MakeFillet == False:
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(TW + w, H + h, 0)
                p4 = vec(TW + w, TW + h, 0)
                p5 = vec(W + w, TW + h, 0)
                p6 = vec(W + w, 0 + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6])

            if obj.MakeFillet == True:
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(TW - r + w, H + h, 0)
                p4 = vec(TW + w, H - r + h, 0)
                p5 = vec(TW + w, TW + R + h, 0)
                p6 = vec(TW + R + w, TW + h, 0)
                p7 = vec(W - r + w, TW + h, 0)
                p8 = vec(W + w, TW - r + h, 0)
                p9 = vec(W + w, 0 + h, 0)
                c1 = vec(TW - r + w, H - r + h, 0)
                c2 = vec(TW + R + w, TW + R + h, 0)
                c3 = vec(W - r + w, TW - r + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p4, p5)
                L4 = Part.makeLine(p6, p7)
                L5 = Part.makeLine(p8, p9)
                L6 = Part.makeLine(p9, p1)
                A1 = Part.makeCircle(r, c1, d, 0, 90)
                A2 = Part.makeCircle(R, c2, d, 180, 270)
                A3 = Part.makeCircle(r, c3, d, 0, 90)

                wire1 = Part.Wire([L1, L2, A1, L3, A2, L4, A3, L5, L6])

            p = Part.Face(wire1)

        if (
            obj.Family == "Flat Sections"
            or obj.Family == "Square"
            or obj.Family == "Square Hollow"
            or obj.Family == "Rectangular Hollow"
        ):
            wire1 = wire2 = 0

            if obj.Family == "Square" or obj.Family == "Flat Sections":
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(W + w, H + h, 0)
                p4 = vec(W + w, 0 + h, 0)
                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                wire1 = Part.Wire([L1, L2, L3, L4])

            if obj.MakeFillet == False and (obj.Family == "Square Hollow" or obj.Family == "Rectangular Hollow"):
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, H + h, 0)
                p3 = vec(W + w, H + h, 0)
                p4 = vec(W + w, 0 + h, 0)
                p5 = vec(TW + w, TW + h, 0)
                p6 = vec(TW + w, H + h - TW, 0)
                p7 = vec(W + w - TW, H + h - TW, 0)
                p8 = vec(W + w - TW, TW + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p1)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p5)

                wire1 = Part.Wire([L1, L2, L3, L4])
                wire2 = Part.Wire([L5, L6, L7, L8])

            if obj.MakeFillet == True and (obj.Family == "Square Hollow" or obj.Family == "Rectangular Hollow"):
                p1 = vec(0 + w, 0 + R + h, 0)
                p2 = vec(0 + w, H - R + h, 0)
                p3 = vec(R + w, H + h, 0)
                p4 = vec(W - R + w, H + h, 0)
                p5 = vec(W + w, H - R + h, 0)
                p6 = vec(W + w, R + h, 0)
                p7 = vec(W - R + w, 0 + h, 0)
                p8 = vec(R + w, 0 + h, 0)

                c1 = vec(R + w, R + h, 0)
                c2 = vec(R + w, H - R + h, 0)
                c3 = vec(W - R + w, H - R + h, 0)
                c4 = vec(W - R + w, R + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(R, c1, d, 180, 270)
                A2 = Part.makeCircle(R, c2, d, 90, 180)
                A3 = Part.makeCircle(R, c3, d, 0, 90)
                A4 = Part.makeCircle(R, c4, d, 270, 0)

                wire1 = Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

                p1 = vec(TW + w, TW + r + h, 0)
                p2 = vec(TW + w, H - TW - r + h, 0)
                p3 = vec(TW + r + w, H - TW + h, 0)
                p4 = vec(W - TW - r + w, H - TW + h, 0)
                p5 = vec(W - TW + w, H - TW - r + h, 0)
                p6 = vec(W - TW + w, TW + r + h, 0)
                p7 = vec(W - TW - r + w, TW + h, 0)
                p8 = vec(TW + r + w, TW + h, 0)

                c1 = vec(TW + r + w, TW + r + h, 0)
                c2 = vec(TW + r + w, H - TW - r + h, 0)
                c3 = vec(W - TW - r + w, H - TW - r + h, 0)
                c4 = vec(W - TW - r + w, TW + r + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                A1 = Part.makeCircle(r, c1, d, 180, 270)
                A2 = Part.makeCircle(r, c2, d, 90, 180)
                A3 = Part.makeCircle(r, c3, d, 0, 90)
                A4 = Part.makeCircle(r, c4, d, 270, 0)

                wire2 = Part.Wire([L1, A2, L2, A3, L3, A4, L4, A1])

            if wire2:
                p1 = Part.Face(wire1)
                p2 = Part.Face(wire2)
                p = p1.cut(p2)
            else:
                p = Part.Face(wire1)

        if obj.Family == "UPE" or obj.Family == "UPN":
            if obj.MakeFillet == False:  # UPE ou UPN sans arrondis

                Yd = 0
                if obj.UPN == True:
                    Yd = (W / 4) * math.tan(math.pi * obj.FlangeAngle / 180)

                p1 = vec(w, h, 0)
                p2 = vec(w, H + h, 0)
                p3 = vec(w + W, H + h, 0)
                p4 = vec(W + w, h, 0)
                p5 = vec(W + w + Yd - TW, h, 0)
                p6 = vec(W + w - Yd - TW, H + h - TF, 0)
                p7 = vec(w + TW + Yd, H + h - TF, 0)
                p8 = vec(w + TW - Yd, h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8])

            if obj.MakeFillet == True and obj.UPN == False:  # UPE avec arrondis

                p1 = vec(w, h, 0)
                p2 = vec(w, H + h, 0)
                p3 = vec(w + W, H + h, 0)
                p4 = vec(W + w, h, 0)
                p5 = vec(W + w - TW + r, h, 0)
                p6 = vec(W + w - TW, h + r, 0)
                p7 = vec(W + w - TW, H + h - TF - R, 0)
                p8 = vec(W + w - TW - R, H + h - TF, 0)
                p9 = vec(w + TW + R, H + h - TF, 0)
                p10 = vec(w + TW, H + h - TF - R, 0)
                p11 = vec(w + TW, h + r, 0)
                p12 = vec(w + TW - r, h, 0)

                C1 = vec(w + TW - r, h + r, 0)
                C2 = vec(w + TW + R, H + h - TF - R, 0)
                C3 = vec(W + w - TW - R, H + h - TF - R, 0)
                C4 = vec(W + w - TW + r, r + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p10, p11)
                L8 = Part.makeLine(p12, p1)

                A1 = Part.makeCircle(r, C1, d, 270, 0)
                A2 = Part.makeCircle(R, C2, d, 90, 180)
                A3 = Part.makeCircle(R, C3, d, 0, 90)
                A4 = Part.makeCircle(r, C4, d, 180, 270)

                wire1 = Part.Wire([L1, L2, L3, L4, A4, L5, A3, L6, A2, L7, A1, L8])

            if obj.MakeFillet == True and obj.UPN == True:  # UPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi * angarc / 180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)

                cot1 = r * sina
                y11 = r - cot1
                cot2 = (H / 2 - r) * tana
                cot3 = cot1 * tana
                x11 = TW - cot2 - cot3
                xc1 = TW - cot2 - cot3 - r * cosa
                yc1 = r
                cot8 = (H / 2 - R - TF + R * sina) * tana
                x10 = TW + cot8
                y10 = H - TF - R + R * sina
                xc2 = cot8 + R * cosa + TW
                yc2 = H - TF - R
                x12 = TW - cot2 - cot3 - r * cosa
                y12 = 0
                x9 = cot8 + R * cosa + TW
                y9 = H - TF
                xc3 = W - xc2
                yc3 = yc2
                xc4 = W - xc1
                yc4 = yc1
                x1 = 0
                y1 = 0
                x2 = 0
                y2 = H
                x3 = W
                y3 = H
                x4 = W
                y4 = 0
                x5 = W - x12
                y5 = 0
                x6 = W - x11
                y6 = y11
                x7 = W - x10
                y7 = y10
                x8 = W - x9
                y8 = y9

                c1 = vec(xc1 + w, yc1 + h, 0)
                c2 = vec(xc2 + w, yc2 + h, 0)
                c3 = vec(xc3 + w, yc3 + h, 0)
                c4 = vec(xc4 + w, yc4 + h, 0)

                p1 = vec(x1 + w, y1 + h, 0)
                p2 = vec(x2 + w, y2 + h, 0)
                p3 = vec(x3 + w, y3 + h, 0)
                p4 = vec(x4 + w, y4 + h, 0)
                p5 = vec(x5 + w, y5 + h, 0)
                p6 = vec(x6 + w, y6 + h, 0)
                p7 = vec(x7 + w, y7 + h, 0)
                p8 = vec(x8 + w, y8 + h, 0)
                p9 = vec(x9 + w, y9 + h, 0)
                p10 = vec(x10 + w, y10 + h, 0)
                p11 = vec(x11 + w, y11 + h, 0)
                p12 = vec(x12 + w, y12 + h, 0)

                A1 = Part.makeCircle(r, c1, d, 270, 0 - angarc)
                A2 = Part.makeCircle(R, c2, d, 90, 180 - angarc)
                A3 = Part.makeCircle(R, c3, d, 0 + angarc, 90)
                A4 = Part.makeCircle(r, c4, d, 180 + angarc, 270)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p6, p7)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p10, p11)
                L8 = Part.makeLine(p12, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, A4, L5, A3, L6, A2, L7, A1, L8])

            p = Part.Face(wire1)

        if (
            obj.Family == "IPE"
            or obj.Family == "IPN"
            or obj.Family == "HEA"
            or obj.Family == "HEB"
            or obj.Family == "HEM"
        ):
            XA1 = W / 2 - TW / 2  # face gauche du web
            XA2 = W / 2 + TW / 2  # face droite du web
            if obj.MakeFillet == False:  # IPE ou IPN sans arrondis
                Yd = 0
                if obj.IPN == True:
                    Yd = (W / 4) * math.tan(math.pi * obj.FlangeAngle / 180)

                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, TF + h - Yd, 0)
                p3 = vec(XA1 + w, TF + h + Yd, 0)
                p4 = vec(XA1 + w, H - TF + h - Yd, 0)
                p5 = vec(0 + w, H - TF + h + Yd, 0)
                p6 = vec(0 + w, H + h, 0)
                p7 = vec(W + w, H + h, 0)
                p8 = vec(W + w, H - TF + h + Yd, 0)
                p9 = vec(XA2 + w, H - TF + h - Yd, 0)
                p10 = vec(XA2 + w, TF + h + Yd, 0)
                p11 = vec(W + w, TF + h - Yd, 0)
                p12 = vec(W + w, 0 + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p3, p4)
                L4 = Part.makeLine(p4, p5)
                L5 = Part.makeLine(p5, p6)
                L6 = Part.makeLine(p6, p7)
                L7 = Part.makeLine(p7, p8)
                L8 = Part.makeLine(p8, p9)
                L9 = Part.makeLine(p9, p10)
                L10 = Part.makeLine(p10, p11)
                L11 = Part.makeLine(p11, p12)
                L12 = Part.makeLine(p12, p1)

                wire1 = Part.Wire([L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L11, L12])

            if obj.MakeFillet == True and obj.IPN == False:  # IPE avec arrondis
                p1 = vec(0 + w, 0 + h, 0)
                p2 = vec(0 + w, TF + h, 0)
                p3 = vec(XA1 - R + w, TF + h, 0)
                p4 = vec(XA1 + w, TF + R + h, 0)
                p5 = vec(XA1 + w, H - TF - R + h, 0)
                p6 = vec(XA1 - R + w, H - TF + h, 0)
                p7 = vec(0 + w, H - TF + h, 0)
                p8 = vec(0 + w, H + h, 0)
                p9 = vec(W + w, H + h, 0)
                p10 = vec(W + w, H - TF + h, 0)
                p11 = vec(XA2 + R + w, H - TF + h, 0)
                p12 = vec(XA2 + w, H - TF - R + h, 0)
                p13 = vec(XA2 + w, TF + R + h, 0)
                p14 = vec(XA2 + R + w, TF + h, 0)
                p15 = vec(W + w, TF + h, 0)
                p16 = vec(W + w, 0 + h, 0)

                c1 = vec(XA1 - R + w, TF + R + h, 0)
                c2 = vec(XA1 - R + w, H - TF - R + h, 0)
                c3 = vec(XA2 + R + w, H - TF - R + h, 0)
                c4 = vec(XA2 + R + w, TF + R + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p2, p3)
                L3 = Part.makeLine(p4, p5)
                L4 = Part.makeLine(p6, p7)
                L5 = Part.makeLine(p7, p8)
                L6 = Part.makeLine(p8, p9)
                L7 = Part.makeLine(p9, p10)
                L8 = Part.makeLine(p10, p11)
                L9 = Part.makeLine(p12, p13)
                L10 = Part.makeLine(p14, p15)
                L11 = Part.makeLine(p15, p16)
                L12 = Part.makeLine(p16, p1)

                A1 = Part.makeCircle(R, c1, d, 270, 0)
                A2 = Part.makeCircle(R, c2, d, 0, 90)
                A3 = Part.makeCircle(R, c3, d, 90, 180)
                A4 = Part.makeCircle(R, c4, d, 180, 270)

                wire1 = Part.Wire([L1, L2, A1, L3, A2, L4, L5, L6, L7, L8, A3, L9, A4, L10, L11, L12])

            if obj.MakeFillet == True and obj.IPN == True:  # IPN avec arrondis
                angarc = obj.FlangeAngle
                angrad = math.pi * angarc / 180
                sina = math.sin(angrad)
                cosa = math.cos(angrad)
                tana = math.tan(angrad)
                cot1 = W / 4 * tana  # 1,47
                cot2 = TF - cot1  # 4,42
                cot3 = r * cosa  # 1,98
                cot4 = r - cot3 * tana  # 1,72
                cot5 = cot4 * tana  # 0,24
                cot5 = cot2 + cot5  # 4,66
                cot6 = R * sina  # 0,55
                cot7 = W / 4 - R - TW / 2  # 4,6
                cot8 = cot6 + cot7  # 5,15
                cot9 = cot7 * tana  # 0,72
                cot10 = R * cosa  # 3,96

                xc1 = r
                yc1 = cot5 - cot3
                c1 = vec(xc1 + w, yc1 + h, 0)

                xc2 = W / 2 - TW / 2 - R
                yc2 = cot9 + TF + cot10
                c2 = vec(xc2 + w, yc2 + h, 0)

                xc3 = xc2
                yc3 = H - yc2
                c3 = vec(xc3 + w, yc3 + h, 0)

                xc4 = xc1
                yc4 = H - yc1
                c4 = vec(xc4 + w, yc4 + h, 0)

                xc5 = W - xc1
                yc5 = yc4
                c5 = vec(xc5 + w, yc5 + h, 0)

                xc6 = W - xc2
                yc6 = yc3
                c6 = vec(xc6 + w, yc6 + h, 0)

                xc7 = xc6
                yc7 = yc2
                c7 = vec(xc7 + w, yc7 + h, 0)

                xc8 = xc5
                yc8 = yc1
                c8 = vec(xc8 + w, yc8 + h, 0)

                A1 = Part.makeCircle(r, c1, d, 90 + angarc, 180)
                A2 = Part.makeCircle(R, c2, d, 270 + angarc, 0)
                A3 = Part.makeCircle(R, c3, d, 0, 90 - angarc)
                A4 = Part.makeCircle(r, c4, d, 180, 270 - angarc)
                A5 = Part.makeCircle(r, c5, d, 270 + angarc, 0)
                A6 = Part.makeCircle(R, c6, d, 90 + angarc, 180)
                A7 = Part.makeCircle(R, c7, d, 180, 270 - angarc)
                A8 = Part.makeCircle(r, c8, d, 0, 90 - angarc)

                xp1 = 0
                yp1 = 0
                p1 = vec(xp1 + w, yp1 + h, 0)

                xp2 = 0
                yp2 = cot5 - cot3
                p2 = vec(xp2 + w, yp2 + h, 0)

                xp3 = cot4
                yp3 = cot5
                p3 = vec(xp3 + w, yp3 + h, 0)

                xp4 = W / 4 + cot8
                yp4 = TF + cot9
                p4 = vec(xp4 + w, yp4 + h, 0)

                xp5 = W / 2 - TW / 2
                yp5 = yc2
                p5 = vec(xp5 + w, yp5 + h, 0)

                xp6 = xp5
                yp6 = H - yp5
                p6 = vec(xp6 + w, yp6 + h, 0)

                xp7 = xp4
                yp7 = H - yp4
                p7 = vec(xp7 + w, yp7 + h, 0)

                xp8 = xp3
                yp8 = H - yp3
                p8 = vec(xp8 + w, yp8 + h, 0)

                xp9 = xp2
                yp9 = H - yp2
                p9 = vec(xp9 + w, yp9 + h, 0)

                xp10 = xp1
                yp10 = H
                p10 = vec(xp10 + w, yp10 + h, 0)

                xp11 = W
                yp11 = H
                p11 = vec(xp11 + w, yp11 + h, 0)

                xp12 = xp11
                yp12 = yp9
                p12 = vec(xp12 + w, yp12 + h, 0)

                xp13 = W - xp8
                yp13 = yp8
                p13 = vec(xp13 + w, yp13 + h, 0)

                xp14 = W - xp7
                yp14 = yp7
                p14 = vec(xp14 + w, yp14 + h, 0)

                xp15 = W - xp6
                yp15 = yp6
                p15 = vec(xp15 + w, yp15 + h, 0)

                xp16 = W - xp5
                yp16 = yp5
                p16 = vec(xp16 + w, yp16 + h, 0)

                xp17 = W - xp4
                yp17 = yp4
                p17 = vec(xp17 + w, yp17 + h, 0)

                xp18 = W - xp3
                yp18 = yp3
                p18 = vec(xp18 + w, yp18 + h, 0)

                xp19 = W - xp2
                yp19 = yp2
                p19 = vec(xp19 + w, yp19 + h, 0)

                xp20 = W
                yp20 = 0
                p20 = vec(xp20 + w, yp20 + h, 0)

                L1 = Part.makeLine(p1, p2)
                L2 = Part.makeLine(p3, p4)
                L3 = Part.makeLine(p5, p6)
                L4 = Part.makeLine(p7, p8)
                L5 = Part.makeLine(p9, p10)
                L6 = Part.makeLine(p10, p11)
                L7 = Part.makeLine(p11, p12)
                L8 = Part.makeLine(p13, p14)
                L9 = Part.makeLine(p15, p16)
                L10 = Part.makeLine(p17, p18)
                L11 = Part.makeLine(p19, p20)
                L12 = Part.makeLine(p20, p1)

                wire1 = Part.Wire([L1, A1, L2, A2, L3, A3, L4, A4, L5, L6, L7, A5, L8, A6, L9, A7, L10, A8, L11, L12])

            p = Part.Face(wire1)

        if obj.Family == "Round Bar":
            c = vec(H / 2 + h, H / 2 + h, 0)
            A1 = Part.makeCircle(H / 2, c, d, 0, 360)
            wire1 = Part.Wire([A1])
            p = Part.Face(wire1)

        if obj.Family == "Pipe":
            c = vec(H / 2 + h, H / 2 + h, 0)
            A1 = Part.makeCircle(H / 2, c, d, 0, 360)
            A2 = Part.makeCircle((H - TW) / 2, c, d, 0, 360)
            wire1 = Part.Wire([A1])
            wire2 = Part.Wire([A2])
            p1 = Part.Face(wire1)
            p2 = Part.Face(wire2)
            p = p1.cut(p2)

        if obj.Family == "Custom Profile":
            custom_prof = obj.CustomProfile
            if isinstance(custom_prof.Shape, Part.Wire):
                p = Part.Face(custom_prof.Shape)
            elif isinstance(custom_prof.Shape, Part.Face):
                p = custom_prof.Shape
            else:
                raise ValueError("Custom profile must be a Face or Sketch")

            W, H = p.BoundBox.XLength, p.BoundBox.YLength

        if obj.Family == "V-Slot":
            if H == 20.0 and W == 20.0:
                p = vslot20x20()
            elif H == 20.0 and W == 40.0:
                p = vslot20x40()
            elif H == 20.0 and W == 60.0:
                p = vslot20x60()
            elif H == 20.0 and W == 80.0:
                p = vslot20x80()

        if obj.Family == "T-Slot":
            if H == 20.0 and W == 20.0:
                p = tslot20x20()

        if obj.Family == "T-Slot 3-Slots":
            if H == 20.0 and W == 20.0:
                p = tslot20x20_three_slot()

        if obj.Family == "T-Slot 2-Slots":
            if H == 20.0 and W == 20.0:
                p = tslot20x20_two_slot()

        if obj.Family == "T-Slot 2-Slots Opp":
            if H == 20.0 and W == 20.0:
                p = tslot20x20_two_slot_opp()

        if obj.Family == "T-Slot 1-Slot":
            if H == 20.0 and W == 20.0:
                p = tslot20x20_one_slot()

        if L:
            ProfileFull = p.extrude(vec(0, 0, L))
            obj.Shape = ProfileFull

            if B1Y or B2Y or B1X or B2X or B1Z or B2Z:  # make the bevels:

                hc = 10 * max(H, W)

                ProfileExt = ProfileFull.fuse(p.extrude(vec(0, 0, L + hc / 4)))
                box = Part.makeBox(hc, hc, hc)
                box.translate(vec(-hc / 2 + w, -hc / 2 + h, L))
                pr = vec(0, 0, L)
                box.rotate(pr, vec(0, 1, 0), B2Y)
                if self.bevels_combined == True:
                    box.rotate(pr, vec(0, 0, 1), B2Z)
                else:
                    box.rotate(pr, vec(1, 0, 0), B2X)
                ProfileCut = ProfileExt.cut(box)

                ProfileExt = ProfileCut.fuse(p.extrude(vec(0, 0, -hc / 4)))
                box = Part.makeBox(hc, hc, hc)
                box.translate(vec(-hc / 2 + w, -hc / 2 + h, -hc))
                pr = vec(0, 0, 0)
                box.rotate(pr, vec(0, 1, 0), B1Y)
                if self.bevels_combined == True:
                    box.rotate(pr, vec(0, 0, 1), B1Z)
                else:
                    box.rotate(pr, vec(1, 0, 0), B1X)
                ProfileCut = ProfileExt.cut(box)

                obj.Shape = ProfileCut.removeSplitter()

                # if wire2: obj.Shape = Part.Compound([wire1,wire2])  # OCC Sweep doesn't be able hollow shape yet :-(

        else:
            obj.Shape = Part.Face(wire1)
        obj.Placement = pl
        obj.positionBySupport()
        obj.recompute()


class ViewProviderProfile:
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
        return []

    def onChanged(self, vp, prop):
        """Print the name of the property that has changed"""
        # App.Console.PrintMessage("Change {} property: {}\n".format(str(vp), str(prop)))
        pass

    def onDelete(self, fp, sub):
        return True

    def getIcon(self):
        """Return the icon in XMP format which will appear in the tree view. This method is optional
        and if not defined a default icon is shown.
        """
        return """
                /* XPM */
                static char * profile_xpm[] = {
                "16 16 15 1",
                " 	c None",
                ".	c #000000",
                "+	c #170000",
                "@	c #2E5DA2",
                "#	c #E8A200",
                "$	c #00172E",
                "%	c #A27400",
                "&	c #FFB900",
                "*	c #8B7400",
                "=	c #001717",
                "-	c #D1A200",
                ";	c #B98B00",
                ">	c #17172E",
                ",	c #2E1700",
                "'	c #171700",
                "                ",
                "                ",
                "                ",
                "                ",
                "  ....+.......  ",
                " .@@@@@@@@@@.#. ",
                " .@@@@@@@@@$%&* ",
                " =@@@@@@@@@$-&;.",
                " =@@@@@@@@@>-&;.",
                " >@@@@@@@@@=-&;.",
                " >@@@@@@@@@$%&* ",
                " .@@@@@@@@@@.-, ",
                "  '..'.+...'.'  ",
                "                ",
                "                ",
                "                "};
        	"""

    def dumps(self):
        """
        Called during document saving.
        """
        return None

    def loads(self, state):
        """
        Called during document restore.
        """
        return None

    def setEdit(self, vobj, mode):
        if mode != 0:
            return None

        import freecad.frameforge.edit_profile_tool

        taskd = freecad.frameforge.edit_profile_tool.EditProfileTaskPanel(self.Object)
        Gui.Control.showDialog(taskd)
        return True

    def unsetEdit(self, vobj, mode):
        if mode != 0:
            return None

        Gui.Control.closeDialog()
        return True

    def edit(self):
        FreeCADGui.ActiveDocument.setEdit(self.Object, 0)


class ViewProviderCustomProfile:
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
        return []

    def onChanged(self, vp, prop):
        """Print the name of the property that has changed"""
        # App.Console.PrintMessage("Change {} property: {}\n".format(str(vp), str(prop)))
        pass

    def onDelete(self, fp, sub):
        return True

    def getIcon(self):
        """Return the icon in XMP format which will appear in the tree view. This method is optional
        and if not defined a default icon is shown.
        """
        return """
            /* XPM */
            static char * custom_profile_xpm[] = {
            "16 16 44 1",
            " 	c None",
            ".	c #3463A1",
            "+	c #3465A4",
            "@	c #3464A1",
            "#	c #836628",
            "$	c #FBBC00",
            "%	c #304461",
            "&	c #335C92",
            "*	c #BC8D00",
            "=	c #FFBF00",
            "-	c #324C72",
            ";	c #32619D",
            ">	c #3364A2",
            ",	c #335888",
            "'	c #CF9B00",
            ")	c #B88A00",
            "!	c #1F6267",
            "~	c #27557E",
            "{	c #335889",
            "]	c #CE9B00",
            "^	c #3362A0",
            "/	c #2D578E",
            "(	c #06AE25",
            "_	c #0E9739",
            ":	c #2E5A93",
            "<	c #32619E",
            "[	c #3465A3",
            "}	c #335D93",
            "|	c #BA8C00",
            "1	c #274C7B",
            "2	c #088D24",
            "3	c #03BB1F",
            "4	c #00D61E",
            "5	c #00D41E",
            "6	c #03BC1F",
            "7	c #0A7D27",
            "8	c #3464A2",
            "9	c #7E632C",
            "0	c #FABB00",
            "a	c #03C01F",
            "b	c #00D81E",
            "c	c #05AB20",
            "d	c #01D21E",
            "e	c #01D31E",
            "                ",
            "                ",
            "                ",
            "                ",
            "                ",
            "  .++++++++@#$  ",
            " %+++++++++&*=  ",
            " -+++;>++++,'=) ",
            " -+++!~++++{]=) ",
            "  +^/(_:<[+}|=  ",
            "  1234567/+890  ",
            "    abb         ",
            "    cde         ",
            "                ",
            "                ",
            "                "};
        	"""

    def dumps(self):
        """
        Called during document saving.
        """
        return None

    def loads(self, state):
        """
        Called during document restore.
        """
        return None

    def setEdit(self, vobj, mode):
        return None

    def unsetEdit(self, vobj, mode):
        return None

    def edit(self):
        pass
